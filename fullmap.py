from pokemon_agent.collision import TILESET_WALKABLE

# Memory addresses (from the pokered disassembly).
MAP_BLOCKS = 0xC6E8      # the current map's block layout, with a 3-block border of neighbouring maps
MAP_HEIGHT = 0xD368      # in blocks (1 block = 2x2 walking squares)
MAP_WIDTH = 0xD369
TILESET = 0xD367
BLOCKSET_BANK = 0xD52B   # which ROM bank holds this tileset's block definitions
BLOCKSET_POINTER = 0xD52C  # 2 bytes: where in that bank they start (16 tiles per block)
BORDER = 3               # blocks of neighbouring map stored around each edge


class FullMap:
    """Walkability of every square on the current map, plus a border of the maps next to it."""

    def __init__(self, game):
        self.game = game
        self.width = game.read_memory(MAP_WIDTH) * 2
        self.height = game.read_memory(MAP_HEIGHT) * 2
        self.walkable_tiles = TILESET_WALKABLE.get(game.read_memory(TILESET), frozenset())
        self.bank = game.read_memory(BLOCKSET_BANK)
        self.pointer = game.read_memory(BLOCKSET_POINTER) | (game.read_memory(BLOCKSET_POINTER + 1) << 8)
        self.offset = BORDER * 2
        self.grid = [
            [self.is_walkable(x, y) for x in range(-self.offset, self.width + self.offset)]
            for y in range(-self.offset, self.height + self.offset)
        ]

    def tile_at(self, x, y):
        blocks_per_row = self.width // 2 + BORDER * 2
        block = self.game.read_memory(MAP_BLOCKS + (y // 2 + BORDER) * blocks_per_row + (x // 2 + BORDER))
        # Like the harness, judge each square by the bottom-left tile of its 2x2 tiles.
        address = self.pointer + block * 16 + ((y % 2) * 2 + 1) * 4 + (x % 2) * 2
        return self.game.emulator._pyboy.memory[self.bank, address]

    def is_walkable(self, x, y):
        return self.tile_at(x, y) in self.walkable_tiles

    def to_grid(self, x, y):
        """Map (x, y) -> (row, col) in self.grid."""
        return (y + self.offset, x + self.offset)
