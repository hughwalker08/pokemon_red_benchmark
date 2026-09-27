from pokemon_agent.collision import PLAYER_COL, PLAYER_ROW

from pathfinder import find_path
from screen_text import read_screen_text
from surroundings import MAP_HEIGHT, MAP_WIDTH, direction_to, read_edges, read_people, read_warps

EDGE_TARGET = {"north": (-20, 0), "south": (20, 0), "west": (0, -20), "east": (0, 20)}
EDGE_DIRECTION = {"north": "up", "south": "down", "west": "left", "east": "right"}


def exit_name(game, destination):
    return f"exit to {destination}" if destination in game.visited_maps else "unexplored exit"


def same_door(a, b):
    next_to_each_other = abs(a["x"] - b["x"]) + abs(a["y"] - b["y"]) == 1
    return next_to_each_other and a["to"] == b["to"]


def build_macros(game, state):
    player = state["player"]["position"]
    macros = {}

    added = []
    for number, warp in enumerate(read_warps(game), start=1):
        if warp["x"] == player["x"] and warp["y"] == player["y"]:
            continue
        if any(same_door(warp, other) for other in added):
            continue
        added.append(warp)
        macros[f"go_to_exit_{number}"] = {
            "kind": "exit",
            "target": warp,
            "description": f"Walk to the {exit_name(game, warp['to'])} ({direction_to(player, warp)})",
        }

    for person in read_people(game):
        macros[f"go_to_person_{person['sprite']}"] = {
            "kind": "person",
            "sprite": person["sprite"],
            "description": f"Walk up to the person/object ({direction_to(player, person)}) and face them",
        }

    for edge in read_edges(game, player):
        place = edge["to"] if edge["to"] in game.visited_maps else "somewhere unexplored"
        macros[f"go_{edge['side']}"] = {
            "kind": "edge",
            "side": edge["side"],
            "description": f"Walk off the {edge['side']} edge of the map, toward {place} ({edge['steps']})",
        }

    return macros


def to_grid(player, thing):
    return (PLAYER_ROW + thing["y"] - player["y"], PLAYER_COL + thing["x"] - player["x"])


def direction_towards(player, thing):
    dx, dy = thing["x"] - player["x"], thing["y"] - player["y"]
    if abs(dx) >= abs(dy):
        return "right" if dx > 0 else "left"
    return "down" if dy > 0 else "up"


def push_direction(game, player, last_direction):
    """Doormats sit on the edge of a map and work by pushing off that edge."""
    height = game.read_memory(MAP_HEIGHT) * 2
    width = game.read_memory(MAP_WIDTH) * 2
    if player["y"] == height - 1:
        return "down"
    if player["y"] == 0:
        return "up"
    if player["x"] == 0:
        return "left"
    if player["x"] == width - 1:
        return "right"
    return last_direction


def run_macro(game, macro, max_presses=40):
    state = game.get_state()
    start_map = state["map"]["map_name"]
    last_direction = state["player"]["facing"]
    presses = 0
    stuck_presses = 0

    while presses < max_presses:
        if state["map"]["map_name"] != start_map or read_screen_text(game) or "collision" not in state:
            break

        player = state["player"]["position"]
        people = read_people(game)
        blocked = {to_grid(player, p) for p in people}

        if macro["kind"] == "exit":
            target = macro["target"]
            if (player["x"], player["y"]) == (target["x"], target["y"]):
                state = game.do(push_direction(game, player, last_direction))
                presses += 1
                break
            goal = to_grid(player, target)
        elif macro["kind"] == "person":
            person = next((p for p in people if p["sprite"] == macro["sprite"]), None)
            if person is None:
                break
            if abs(person["x"] - player["x"]) + abs(person["y"] - player["y"]) == 1:
                facing = direction_towards(player, person)
                if state["player"]["facing"] != facing:
                    state = game.do(facing)
                    presses += 1
                break
            goal = to_grid(player, person)
        else:
            row_change, col_change = EDGE_TARGET[macro["side"]]
            goal = (PLAYER_ROW + row_change, PLAYER_COL + col_change)

        path = find_path(state["collision"]["walkable"], (PLAYER_ROW, PLAYER_COL), goal, blocked)
        if not path:
            if macro["kind"] != "edge":
                break
            path = [EDGE_DIRECTION[macro["side"]]]

        position_before = (player["x"], player["y"], state["map"]["map_name"])
        state = game.do(path[0])
        presses += 1
        last_direction = path[0]
        position_after = (state["player"]["position"]["x"], state["player"]["position"]["y"], state["map"]["map_name"])
        stuck_presses = stuck_presses + 1 if position_after == position_before else 0
        if stuck_presses >= 2:
            break

    return state, presses
