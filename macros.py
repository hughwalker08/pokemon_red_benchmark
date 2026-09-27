from fullmap import FullMap
from pathfinder import find_path
from screen_text import read_screen_text
from surroundings import MAP_HEIGHT, MAP_WIDTH, direction_to, read_edges, read_people, read_signs, read_warps

EDGE_DIRECTION = {"north": "up", "south": "down", "west": "left", "east": "right"}


def exit_name(game, destination):
    if destination in game.visited_maps:
        return f"exit to {destination} (been there {game.visited_maps[destination]} times)"
    return "unexplored exit"


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
            "description": f"Walk up to the {person['kind']} ({direction_to(player, person)}) and face it",
        }

    for number, sign in enumerate(read_signs(game), start=1):
        macros[f"go_to_sign_{number}"] = {
            "kind": "sign",
            "target": sign,
            "description": f"Walk up to the sign ({direction_to(player, sign)}) and face it",
        }

    for edge in read_edges(game, player):
        if edge["to"] in game.visited_maps:
            place = f"{edge['to']} (been there {game.visited_maps[edge['to']]} times)"
        else:
            place = "somewhere unexplored"
        macros[f"go_{edge['side']}"] = {
            "kind": "edge",
            "side": edge["side"],
            "description": f"Walk off the {edge['side']} edge of the map, toward {place} ({edge['steps']})",
        }

    return macros


def same_square(a, b):
    return a["x"] == b["x"] and a["y"] == b["y"]


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


def edge_squares(full_map, side):
    """Every square just past the given edge; reaching any of them crosses into the next map."""
    rows = range(len(full_map.grid))
    cols = range(len(full_map.grid[0]))
    if side == "north":
        return {(full_map.offset - 1, c) for c in cols}
    if side == "south":
        return {(full_map.offset + full_map.height, c) for c in cols}
    if side == "west":
        return {(r, full_map.offset - 1) for r in rows}
    return {(r, full_map.offset + full_map.width) for r in rows}


def edge_goal(full_map, player, side):
    """A square just beyond the given edge, in line with the player."""
    x, y = player["x"], player["y"]
    if side == "north":
        y = -1
    elif side == "south":
        y = full_map.height
    elif side == "west":
        x = -1
    else:
        x = full_map.width
    return full_map.to_grid(x, y)


def run_macro(game, macro, max_presses=60):
    state = game.get_state()
    start_map = state["map"]["map_name"]
    last_direction = state["player"]["facing"]
    presses = 0
    stuck_presses = 0
    full_map = FullMap(game)
    other_doors = [w for w in read_warps(game) if macro["kind"] != "exit" or not same_square(w, macro["target"])]

    while presses < max_presses:
        if state["map"]["map_name"] != start_map or read_screen_text(game) or "collision" not in state:
            break

        player = state["player"]["position"]
        people = read_people(game)
        blocked = {full_map.to_grid(p["x"], p["y"]) for p in people}
        blocked |= {full_map.to_grid(w["x"], w["y"]) for w in other_doors if not same_square(w, player)}

        if macro["kind"] == "exit":
            target = macro["target"]
            if same_square(player, target):
                state = game.do(push_direction(game, player, last_direction))
                presses += 1
                break
            goal = full_map.to_grid(target["x"], target["y"])
        elif macro["kind"] in ("person", "sign"):
            if macro["kind"] == "person":
                thing = next((p for p in people if p["sprite"] == macro["sprite"]), None)
            else:
                thing = macro["target"]
            if thing is None:
                break
            if abs(thing["x"] - player["x"]) + abs(thing["y"] - player["y"]) == 1:
                facing = direction_towards(player, thing)
                if state["player"]["facing"] != facing:
                    state = game.do(facing)
                    presses += 1
                break
            goal = full_map.to_grid(thing["x"], thing["y"])
        else:
            goal = edge_goal(full_map, player, macro["side"])

        start = full_map.to_grid(player["x"], player["y"])
        full_map.grid[start[0]][start[1]] = True
        goals = edge_squares(full_map, macro["side"]) if macro["kind"] == "edge" else None
        path = find_path(full_map.grid, start, goal, blocked, goals)
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
