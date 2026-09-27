from pokemon_agent.memory.red import MAP_NAMES

# Memory addresses (from the pokered disassembly).
NUM_WARPS = 0xD3AE       # how many warps (doors/stairs) this map has
WARP_TABLE = 0xD3AF      # 4 bytes per warp: y, x, destination warp, destination map
LAST_MAP = 0xD365        # the outdoor map you came from
NUM_SPRITES = 0xD4E1     # how many characters/objects this map has
SPRITE_DATA_1 = 0xC100   # 16 bytes per sprite; byte 0 = picture (0 means empty)
SPRITE_DATA_2 = 0xC200   # 16 bytes per sprite; bytes 4 and 5 = y and x (plus 4)


def read_warps(game):
    warps = []
    for i in range(game.read_memory(NUM_WARPS)):
        start = WARP_TABLE + 4 * i
        y = game.read_memory(start)
        x = game.read_memory(start + 1)
        dest_map = game.read_memory(start + 3)
        if dest_map == 255:
            dest_map = game.read_memory(LAST_MAP)
        warps.append({"x": x, "y": y, "to": MAP_NAMES.get(dest_map, f"map {dest_map}")})
    return warps


def read_people(game):
    people = []
    for i in range(1, game.read_memory(NUM_SPRITES) + 1):
        if game.read_memory(SPRITE_DATA_1 + 16 * i) == 0:
            continue
        y = game.read_memory(SPRITE_DATA_2 + 16 * i + 4) - 4
        x = game.read_memory(SPRITE_DATA_2 + 16 * i + 5) - 4
        people.append({"x": x, "y": y})
    return people


def direction_to(player, target):
    dx = target["x"] - player["x"]
    dy = target["y"] - player["y"]
    parts = []
    if dx > 0:
        parts.append(f"{dx} right")
    if dx < 0:
        parts.append(f"{-dx} left")
    if dy > 0:
        parts.append(f"{dy} down")
    if dy < 0:
        parts.append(f"{-dy} up")
    return ", ".join(parts) or "here"


def describe_surroundings(game, state):
    player = state["player"]["position"]
    lines = []
    for warp in read_warps(game):
        if warp["to"] in game.visited_maps:
            lines.append(f"Exit to {warp['to']}: {direction_to(player, warp)}")
        else:
            lines.append(f"Exit (unexplored): {direction_to(player, warp)}")
    for person in read_people(game):
        lines.append(f"Person/object: {direction_to(player, person)}")
    return lines
