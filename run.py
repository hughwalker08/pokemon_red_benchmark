import argparse

from actions import allowed_buttons
from game import Game
from jev import ask_jev
from memory import History, describe_effect
from screen_text import read_screen_text
from state_text import state_to_text
from surroundings import describe_surroundings

STANDING_GOAL = "Make progress in the main story toward the next badge."


def run(steps, watch, start_save):
    game = Game(watch=watch)
    state = game.load(start_save)
    total_cost = 0.0
    history = History(length=10)
    screen_text = read_screen_text(game)

    for step in range(1, steps + 1):
        text = state_to_text(state, describe_surroundings(game, state), screen_text)
        text += "\n" + history.to_text()
        buttons = allowed_buttons(game, state, screen_text)
        result = ask_jev(text, STANDING_GOAL, buttons)

        new_state = game.do(result["button"])
        new_screen_text = read_screen_text(game)
        history.record(result["button"], describe_effect(state, new_state, screen_text, new_screen_text))
        state, screen_text = new_state, new_screen_text
        total_cost += result["cost"]

        ranked = sorted(result["probabilities"].items(), key=lambda item: item[1], reverse=True)
        top = ", ".join(f"{button} {p:.2f}" for button, p in ranked[:3])
        position = state["player"]["position"]
        print(f"step {step:4}  {state['map']['map_name']} ({position['x']},{position['y']})")
        print(f"           chose {result['button']:6} confidence {result['confidence']:.2f}   top: {top}")

    print(f"\nDone: {steps} steps, total cost ${total_cost:.5f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--start", default="new_game_bedroom")
    args = parser.parse_args()
    run(args.steps, args.watch, args.start)
