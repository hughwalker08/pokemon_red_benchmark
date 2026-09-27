import argparse
import random

from actions import allowed_buttons, describe_front
from config import JEV_MODEL
from game import Game
from jev import ask_jev
from memory import History, describe_effect
from run_log import RunLog
from screen_text import read_screen_text
from state_text import state_to_text
from surroundings import describe_surroundings

STANDING_GOAL = "Make progress in the main story toward the next badge."
TEMPERATURE = 0.5  # 1 = sample Jev's probabilities as-is; lower = follow Jev's top choice more often


def pick_button(probabilities, rng, temperature):
    buttons = list(probabilities.keys())
    weights = [p ** (1 / temperature) for p in probabilities.values()]
    if sum(weights) == 0:
        return max(probabilities, key=probabilities.get)
    return rng.choices(buttons, weights=weights)[0]


def run(steps, watch, start_save, seed):
    rng = random.Random(seed)
    game = Game(watch=watch)
    state = game.load(start_save)
    screen_text = read_screen_text(game)
    history = History(length=10)
    log = RunLog("armA", {"arm": "A", "start_save": start_save, "goal": STANDING_GOAL, "jev_model": JEV_MODEL, "seed": seed, "temperature": TEMPERATURE})
    total_cost = 0.0
    step = 0

    try:
        for step in range(1, steps + 1):
            state, screen_text, cost = play_step(game, step, state, screen_text, history, log, rng)
            total_cost += cost
    finally:
        log.finish({
            "steps_completed": step,
            "total_cost": total_cost,
            "final_map": state["map"]["map_name"],
            "final_position": state["player"]["position"],
            "badges": state["player"]["badge_count"],
            "maps_visited": sorted(game.visited_maps),
        })
        print(f"\nDone: {step} steps, total cost ${total_cost:.5f}, log in {log.folder}")


def play_step(game, step, state, screen_text, history, log, rng):
    surroundings = describe_surroundings(game, state)
    if "collision" in state:
        surroundings.insert(0, describe_front(game, state))
    text = state_to_text(state, surroundings, screen_text)
    text += "\n" + history.to_text()
    buttons = allowed_buttons(game, state, screen_text)
    result = ask_jev(text, STANDING_GOAL, buttons)
    button = pick_button(result["probabilities"], rng, TEMPERATURE)
    screen_before = game.emulator.get_screen().copy()

    new_state = game.do(button)
    new_screen_text = read_screen_text(game)
    effect = describe_effect(state, new_state, screen_text, new_screen_text)
    history.record(button, effect)

    log.log_step(step, {
        "map": state["map"]["map_name"],
        "position": state["player"]["position"],
        "state_text": text,
        "goal": STANDING_GOAL,
        "buttons_offered": buttons,
        "jev_top_choice": result["button"],
        "button": button,
        "confidence": result["confidence"],
        "probabilities": result["probabilities"],
        "cost": result["cost"],
        "effect": effect,
    }, screen_before)

    ranked = sorted(result["probabilities"].items(), key=lambda item: item[1], reverse=True)
    top = ", ".join(f"{button} {p:.2f}" for button, p in ranked[:3])
    position = new_state["player"]["position"]
    print(f"step {step:4}  {new_state['map']['map_name']} ({position['x']},{position['y']})")
    print(f"           pressed {button:6} (Jev's top: {result['button']}, confidence {result['confidence']:.2f})   top: {top}   -> {effect}")

    return new_state, new_screen_text, result["cost"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--start", default="new_game_bedroom")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    run(args.steps, args.watch, args.start, args.seed)
