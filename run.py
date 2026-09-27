import argparse
import random

from actions import allowed_buttons, describe_front
from config import JEV_MODEL, SOL_MODEL
from dialogue import advance_dialogue, is_plain_dialogue
from game import Game
from jev import BUTTON_DESCRIPTIONS, ask_jev
from macros import build_macros, run_macro
from memory import History, describe_effect
from milestones import MILESTONES, MilestoneTracker
from run_log import RunLog
from screen_text import read_screen_text
from sol import ask_sol
from state_text import state_to_text
from surroundings import describe_surroundings

STANDING_GOAL = "Make progress in the main story toward the next badge."
DEFAULT_TEMPERATURE = 0.5  # 1 = sample Jev's probabilities as-is; lower = follow Jev's top choice more often


def pick_button(probabilities, rng, temperature):
    buttons = list(probabilities.keys())
    weights = [p ** (1 / temperature) for p in probabilities.values()]
    if sum(weights) == 0:
        return max(probabilities, key=probabilities.get)
    return rng.choices(buttons, weights=weights)[0]


def run(steps, watch, start_save, seed, arm, plan_every, stuck_limit, tag, temperature):
    rng = random.Random(seed)
    game = Game(watch=watch)
    state = game.load(start_save)
    screen_text = read_screen_text(game)
    history = History(length=10)       # what Jev sees
    sol_history = History(length=30)   # Sol gets a longer view
    goal = STANDING_GOAL
    settings = {"arm": arm, "start_save": start_save, "jev_model": JEV_MODEL, "seed": seed,
                "temperature": temperature, "max_steps": steps, "stuck_limit": stuck_limit, "tag": tag}
    if arm == "B":
        settings.update({"sol_model": SOL_MODEL, "plan_every": plan_every})
    log = RunLog(f"arm{arm}_seed{seed}" + (f"_{tag}" if tag else ""), settings)
    milestones = MilestoneTracker()
    costs = {"jev": 0.0, "sol": 0.0}
    step = 0

    try:
        for step in range(1, steps + 1):
            plan_now = arm == "B" and (step - 1) % plan_every == 0
            state, screen_text, goal, step_costs = play_step(
                game, step, state, screen_text, history, sol_history, log, rng, goal, plan_now, milestones, temperature
            )
            costs["jev"] += step_costs["jev"]
            costs["sol"] += step_costs["sol"]
            last_progress = max(milestones.reached.values(), default=0)
            if step - last_progress >= stuck_limit:
                print(f"\nNo new milestone for {stuck_limit} steps - ending the run early.")
                break
    finally:
        log.finish({
            "steps_completed": step,
            "milestone_score": milestones.score(),
            "milestones": milestones.reached,
            "jev_cost": costs["jev"],
            "sol_cost": costs["sol"],
            "total_cost": costs["jev"] + costs["sol"],
            "final_map": state["map"]["map_name"],
            "final_position": state["player"]["position"],
            "badges": state["player"]["badge_count"],
            "maps_visited": dict(game.visited_maps),
        })
        total = costs["jev"] + costs["sol"]
        print(f"\nDone: {step} steps, cost ${total:.4f} (Jev ${costs['jev']:.4f}, Sol ${costs['sol']:.4f}), log in {log.folder}")
        print(f"Milestones ({milestones.score()}/{len(MILESTONES)}): {milestones.reached}")


def play_step(game, step, state, screen_text, history, sol_history, log, rng, goal, plan_now, milestones, temperature):
    surroundings = describe_surroundings(game, state)
    if "collision" in state:
        surroundings.insert(0, describe_front(game, state))
    state_text = state_to_text(state, surroundings, screen_text)
    jev_text = state_text + "\n" + history.to_text()

    buttons = allowed_buttons(game, state, screen_text)
    options = {button: BUTTON_DESCRIPTIONS[button] for button in buttons}
    macros = {}
    if not screen_text and "collision" in state:
        macros = build_macros(game, state)
        options.update({name: macro["description"] for name, macro in macros.items()})

    sol_cost = 0.0
    if plan_now:
        plan = ask_sol(state_text, sol_history.to_text(), options, goal)
        goal, sol_cost = plan["goal"], plan["cost"]
        print(f"   SOL goal: {goal}")

    result = ask_jev(jev_text, goal, options)
    button = pick_button(result["probabilities"], rng, temperature)
    screen_before = game.emulator.get_screen().copy()

    if button in macros:
        new_state, presses = run_macro(game, macros[button])
        label = macros[button]["description"]
    else:
        new_state, presses = game.do(button), 1
        label = button
    new_screen_text = read_screen_text(game)
    effect = describe_effect(state, new_state, screen_text, new_screen_text)

    if is_plain_dialogue(game, new_screen_text):
        transcript, extra_presses = advance_dialogue(game)
        presses += extra_presses
        effect = f'text: "{" ".join(transcript)[:250]}"'
        new_state, new_screen_text = game.get_state(), read_screen_text(game)
    history.record(label, effect)
    sol_history.record(label, effect)
    new_milestones = milestones.update(step, new_state, effect, game)
    for name in new_milestones:
        print(f"   *** MILESTONE: {name} (step {step})")

    log.log_step(step, {
        "map": state["map"]["map_name"],
        "position": state["player"]["position"],
        "state_text": jev_text,
        "goal": goal,
        "planned_this_step": plan_now,
        "options_offered": options,
        "jev_top_choice": result["button"],
        "button": button,
        "presses": presses,
        "confidence": result["confidence"],
        "probabilities": result["probabilities"],
        "cost": result["cost"],
        "sol_cost": sol_cost,
        "effect": effect,
        "new_milestones": new_milestones,
    }, screen_before)

    position = new_state["player"]["position"]
    print(f"step {step:4}  {new_state['map']['map_name']} ({position['x']},{position['y']})")
    print(f"           did {label[:45]:45} (Jev's top: {result['button']}, conf {result['confidence']:.2f})   -> {effect}")

    return new_state, new_screen_text, goal, {"jev": result["cost"], "sol": sol_cost}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--start", default="new_game_bedroom")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--arm", choices=["A", "B"], default="A")
    parser.add_argument("--plan-every", type=int, default=15)
    parser.add_argument("--stuck-limit", type=int, default=1000, help="end early after this many steps with no new milestone")
    parser.add_argument("--tag", default="", help="label for this batch of runs, e.g. v2 (used by compare.py)")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE, help="1 = pick options at Jev's own probabilities")
    args = parser.parse_args()
    run(args.steps, args.watch, args.start, args.seed, args.arm, args.plan_every, args.stuck_limit, args.tag, args.temperature)
