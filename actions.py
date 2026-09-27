from pokemon_agent.collision import PLAYER_COL, PLAYER_ROW

from game import BUTTONS
from surroundings import read_people

# How each direction changes (row, column) on the grid, and (x, y) on the map.
GRID_STEP = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
MAP_STEP = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def is_blocked(game, state, direction):
    row_change, col_change = GRID_STEP[direction]
    if not state["collision"]["walkable"][PLAYER_ROW + row_change][PLAYER_COL + col_change]:
        return True

    x_change, y_change = MAP_STEP[direction]
    player = state["player"]["position"]
    target = {"x": player["x"] + x_change, "y": player["y"] + y_change}
    return target in read_people(game)


def allowed_buttons(game, state, screen_text):
    if screen_text or state["battle"]["in_battle"]:
        return BUTTONS

    allowed = []
    for button in BUTTONS:
        if button in GRID_STEP and button == state["player"]["facing"] and is_blocked(game, state, button):
            continue
        allowed.append(button)
    return allowed
