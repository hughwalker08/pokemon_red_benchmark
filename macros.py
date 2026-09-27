from surroundings import direction_to, read_edges, read_people, read_warps


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
