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


def is_blocked(game, state, direction):
    if not square_walkable(state, direction):
        return True
    return square_position(state, direction) in read_people(game)


def describe_front(game, state):
    facing = state["player"]["facing"]
    target = square_position(state, facing)
    if target in read_people(game):
        return "In front of you: a person or object (press a to talk/interact)"
    if any(warp["x"] == target["x"] and warp["y"] == target["y"] for warp in read_warps(game)):
        return "In front of you: an exit (walk onto it to use it)"
    if not square_walkable(state, facing):
        return "In front of you: something solid (wall, furniture, sign or counter)"
    return "In front of you: open floor (nothing to interact with)"


def allowed_buttons(game, state, screen_text):
    if screen_text or state["battle"]["in_battle"]:
        return BUTTONS

    allowed = []
    for button in BUTTONS:
        if button in GRID_STEP and button == state["player"]["facing"] and is_blocked(game, state, button):
            continue
        allowed.append(button)
    return allowed
