import requests

from config import JEV_ENDPOINT, JEV_MODEL, OPENROUTER_API_KEY

BUTTON_DESCRIPTIONS = {
    "up": "walk up one tile, or move a menu cursor up",
    "down": "walk down one tile, or move a menu cursor down",
    "left": "walk left one tile, or move a menu cursor left",
    "right": "walk right one tile, or move a menu cursor right",
    "a": "talk / interact with what you face, confirm a menu option, advance text",
    "b": "cancel / close a menu, go back",
    "start": "open the main menu",
    "select": "rarely useful",
}

INSTRUCTIONS = "You are playing Pokemon Red. Pick the single option that makes the most progress toward the goal."


def ask_jev(state_text, goal, options):
    request_body = {
        "model": JEV_MODEL,
        "state": {"goal": goal, "game": state_text},
        "questions": {
            "action": {
                "type": "choice",
                "instructions": INSTRUCTIONS,
                "criteria": options,
            }
        },
    }
    response = requests.post(
        JEV_ENDPOINT,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json=request_body,
        timeout=30,
    )
    response.raise_for_status()
    reply = response.json()

    answer = reply["answers"]["action"]
    return {
        "button": answer["choice"],
        "confidence": answer["confidence"],
        "probabilities": answer["probabilities"],
        "cost": reply["usage"]["cost"],
    }
