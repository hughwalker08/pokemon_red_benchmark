from map_names import map_name

# Memory addresses (from the pokered disassembly).
NUM_WARPS = 0xD3AE       # how many warps (doors/stairs) this map has
WARP_TABLE = 0xD3AF      # 4 bytes per warp: y, x, destination warp, destination map
LAST_MAP = 0xD365        # the outdoor map you came from
NUM_SPRITES = 0xD4E1     # how many characters/objects this map has
SPRITE_DATA_1 = 0xC100   # 16 bytes per sprite; byte 0 = picture (0 means empty)
SPRITE_DATA_2 = 0xC200   # 16 bytes per sprite; bytes 4 and 5 = y and x (plus 4)
# What a sprite looks like, by its picture number (checked in Oak's Lab); anything else is a person.
SPRITE_KINDS = {61: "Poké Ball", 65: "book"}
MISSABLE_LIST = 0xD5CE  # pairs of (sprite number, missable number), ends with 255
MISSABLE_FLAGS = 0xD5A6  # one bit per missable number; 1 means hidden
NUM_SIGNS = 0xD4B0       # how many signs this map has
SIGN_TABLE = 0xD4B1      # 2 bytes per sign: y, x
MAP_HEIGHT = 0xD368    # in blocks (1 block = 2x2 tiles)
MAP_WIDTH = 0xD369
CONNECTIONS = 0xD370     # one on/off bit per edge: north=8, south=4, west=2, east=1
EDGE_MAP = {"north": 0xD371, "south": 0xD37C, "west": 0xD387, "east": 0xD392}
EDGE_BIT = {"north": 8, "south": 4, "west": 2, "east": 1}


def read_warps(game):
    warps = []
    for i in range(game.read_memory(NUM_WARPS)):
        start = WARP_TABLE + 4 * i
        y = game.read_memory(start)
        x = game.read_memory(start + 1)
        dest_map = game.read_memory(start + 3)
        if dest_map == 255:
            dest_map = game.read_memory(LAST_MAP)
        warps.append({"x": x, "y": y, "to": map_name(dest_map)})
    return warps


def read_signs(game):
    signs = []
    for i in range(game.read_memory(NUM_SIGNS)):
        y = game.read_memory(SIGN_TABLE + 2 * i)
        x = game.read_memory(SIGN_TABLE + 2 * i + 1)
        signs.append({"x": x, "y": y})
    return signs


def is_hidden(game, sprite):
    address = MISSABLE_LIST
    while game.read_memory(address) != 255:
        if game.read_memory(address) == sprite:
            missable = game.read_memory(address + 1)
            flags = game.read_memory(MISSABLE_FLAGS + missable // 8)
            return flags & (1 << (missable % 8)) != 0
        address += 2
    return False


def read_people(game):
    people = []
    for i in range(1, game.read_memory(NUM_SPRITES) + 1):
        if game.read_memory(SPRITE_DATA_1 + 16 * i) == 0:
            continue
        if is_hidden(game, i):
            continue
        y = game.read_memory(SPRITE_DATA_2 + 16 * i + 4) - 4
        x = game.read_memory(SPRITE_DATA_2 + 16 * i + 5) - 4
        picture = game.read_memory(SPRITE_DATA_1 + 16 * i)
        people.append({"x": x, "y": y, "sprite": i, "kind": SPRITE_KINDS.get(picture, "person")})
    return people


def read_edges(game, player):
    height = game.read_memory(MAP_HEIGHT) * 2
    width = game.read_memory(MAP_WIDTH) * 2
    steps = {
        "north": f"{player['y'] + 1} up",
        "south": f"{height - player['y']} down",
        "west": f"{player['x'] + 1} left",
        "east": f"{width - player['x']} right",
    }
    edges = []
    connections = game.read_memory(CONNECTIONS)
    for side in ["north", "south", "west", "east"]:
        if connections & EDGE_BIT[side]:
            dest_map = game.read_memory(EDGE_MAP[side])
            edges.append({"side": side, "to": map_name(dest_map), "steps": steps[side]})
    return edges


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
    for edge in read_edges(game, player):
        if edge["to"] in game.visited_maps:
            lines.append(f"{edge['side'].capitalize()} edge leads to {edge['to']}: {edge['steps']}")
        else:
            lines.append(f"{edge['side'].capitalize()} edge leads somewhere unexplored: {edge['steps']}")
    for person in read_people(game):
        kind = person["kind"]
        lines.append(f"{kind[0].upper() + kind[1:]}: {direction_to(player, person)}")
    for sign in read_signs(game):
        lines.append(f"Sign: {direction_to(player, sign)}")
    return lines
