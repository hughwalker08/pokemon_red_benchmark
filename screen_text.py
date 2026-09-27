from pokemon_agent.memory.red import GEN1_ENCODING

SCREEN = 0xC3A0     # the 20x18 grid of tiles currently on screen
WIDTH = 20
HEIGHT = 18

CHARACTERS = dict(GEN1_ENCODING)
CHARACTERS.update({0x9A: "(", 0x9B: ")", 0x9C: ":", 0xBA: "é", 0xED: "▶", 0xEE: "▼", 0xEF: "♂"})


def read_screen_text(game):
    lines = []
    for row in range(HEIGHT):
        line = ""
        has_letters = False
        for col in range(WIDTH):
            tile = game.read_memory(SCREEN + row * WIDTH + col)
            if tile >= 0x80:
                has_letters = True
                line += CHARACTERS.get(tile, "?")
            else:
                line += " "
        if has_letters:
            lines.append(line.rstrip())
    return lines
