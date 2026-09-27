import time

import requests

from config import OPENROUTER_API_KEY, SOL_ENDPOINT, SOL_MODEL

SYSTEM_PROMPT = """You are the planner for an agent playing Pokemon Red. The agent itself is a simple decision model:
every step it reads the game state and picks ONE option from a list. You cannot press buttons; you only set its goal.

Your job: read the state and recent history, then write the agent's next goal.
- Focus only on progressing the main story (the next badge and the required story events).
- The goal must be ONE short sentence (at most two steps, e.g. "leave the house, then ...") that stays
  useful for the next ~15 steps.
- Name places by what they are, never by step counts, because the agent keeps moving and counts go out
  of date: "the exit at the bottom of the room", "the north edge of Pallet Town", "the Poke Ball on the table".
- Use the same kinds of words as the agent's options ("walk to the exit", "walk off the north edge",
  "walk up to the Poke Ball and face it, then press a") so the agent recognises them.
- If the recent history shows the agent repeating itself, give a different goal that breaks the loop.
Reply with the goal sentence only."""


def ask_sol(state_text, history_text, options, current_goal):
    option_lines = "\n".join(f"- {description}" for description in options.values())
    user_message = (
        f"Current goal: {current_goal}\n\n"
        f"Game state:\n{state_text}\n\n"
        f"Recent history:\n{history_text}\n\n"
        f"The agent's options right now:\n{option_lines}"
    )
    request_body = {
        "model": SOL_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "reasoning": {"effort": "low"},
        "max_tokens": 300,
    }

    for attempt, wait in enumerate([5, 30, 120, None], start=1):
        try:
            response = requests.post(
                SOL_ENDPOINT,
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json=request_body,
                timeout=60,
            )
            response.raise_for_status()
            break
        except requests.RequestException as error:
            if wait is None:
                raise
            print(f"   Sol request failed (attempt {attempt}: {error.__class__.__name__}), retrying in {wait}s")
            time.sleep(wait)

    reply = response.json()
    goal = (reply["choices"][0]["message"]["content"] or "").strip()
    return {"goal": goal or current_goal, "cost": reply["usage"]["cost"]}
