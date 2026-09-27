from pokemon_agent.collision import PLAYER_COL, PLAYER_ROW

from game import BUTTONS
from surroundings import read_people, read_warps

# How each direction changes (row, column) on the grid, and (x, y) on the map.
GRID_STEP = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
MAP_STEP = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def square_walkable(state, direction):
    row_change, col_change = GRID_STEP[direction]
    return state["collision"]["walkable"][PLAYER_ROW + row_change][PLAYER_COL + col_change]


def square_position(state, direction):
    x_change, y_change = MAP_STEP[direction]
    player = state["player"]["position"]
    return {"x": player["x"] + x_change, "y": player["y"] + y_change}


def person_at(game, position):
    return any(p["x"] == position["x"] and p["y"] == position["y"] for p in read_people(game))


def is_blocked(game, state, direction):
    if not square_walkable(state, direction):
        return True
    return person_at(game, square_position(state, direction))


def standing_on_exit(game, state):
    player = state["player"]["position"]
    return any(warp["x"] == player["x"] and warp["y"] == player["y"] for warp in read_warps(game))


def describe_front(game, state):
    facing = state["player"]["facing"]
    target = square_position(state, facing)
    thing = next((p for p in read_people(game) if p["x"] == target["x"] and p["y"] == target["y"]), None)
    if thing:
        front = f"In front of you: a {thing['kind']}"
    elif any(warp["x"] == target["x"] and warp["y"] == target["y"] for warp in read_warps(game)):
        front = "In front of you: an exit"
    elif not square_walkable(state, facing):
        front = "In front of you: something solid (wall, furniture, sign or counter)"
    else:
        front = "In front of you: open floor"
    if standing_on_exit(game, state):
        front = "You are standing on an exit.\n" + front
    return front


def allowed_buttons(game, state, screen_text):
    if screen_text or state["battle"]["in_battle"] or standing_on_exit(game, state):
        return BUTTONS

    allowed = []
    for button in BUTTONS:
        if button in GRID_STEP and button == state["player"]["facing"] and is_blocked(game, state, button):
            continue
        allowed.append(button)
    return allowed
