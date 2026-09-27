from collections import Counter

from pokemon_agent.collision import build_collision_grid, render_ascii_map
from pokemon_agent.emulator import create_emulator
from pokemon_agent.memory.red import PokemonRedReader
from pokemon_agent.state.builder import build_game_state
from pyboy import PyBoy

from screen_text import read_screen_text

ROM_PATH = "roms/pokemon_red.gb"
BUTTONS = ["up", "down", "left", "right", "a", "b", "start", "select"]
MAP_ID = 0xD35E  # which map you're on; when it changes, the screen fades and input is ignored
SCREEN = 0xC3A0  # the 20x18 tiles currently on screen
SCREEN_SIZE = 20 * 18
ENEMY_HP = 0xCFE6    # 2 bytes, the active enemy Pokémon's current HP
ENEMY_MAX_HP = 0xCFF4
JOY_IGNORE = 0xCD6B  # 0xFF while a scripted scene is running and every button is ignored


class Game:
    def __init__(self, watch=False):
        self.emulator = create_emulator(ROM_PATH)
        if watch:
            self.emulator._pyboy.stop(save=False)
            self.emulator._pyboy = PyBoy(ROM_PATH, window="SDL2")
        self.reader = PokemonRedReader(self.emulator)
        self.visited_maps = Counter()
        self.current_map = None

    def get_state(self):
        state = build_game_state(self.reader)
        map_name = state["map"]["map_name"]
        if map_name != self.current_map:
            self.visited_maps[map_name] += 1
            self.current_map = map_name
        enemy = state["battle"].get("enemy")
        if state["battle"]["in_battle"] and enemy:
            # The harness reads a stale copy; the active enemy's HP lives here (pokered wEnemyMonHP/MaxHP).
            enemy["hp"] = self.read_memory(ENEMY_HP) << 8 | self.read_memory(ENEMY_HP + 1)
            enemy["max_hp"] = self.read_memory(ENEMY_MAX_HP) << 8 | self.read_memory(ENEMY_MAX_HP + 1)
        if not state["battle"]["in_battle"]:
            collision = build_collision_grid(self.emulator)
            collision["ascii"] = render_ascii_map(collision, legend=True)
            state["collision"] = collision
        return state

    def do(self, button):
        if button not in BUTTONS:
            raise ValueError(f"Unknown button: {button}")
        map_before = self.read_memory(MAP_ID)
        hold = 3 if button in ("a", "b") else 8
        self.emulator.press(button, hold)
        self.emulator.tick(20 - hold)
        if self.read_memory(MAP_ID) != map_before:
            self.emulator.tick(120)
        self.wait_while_input_ignored()
        return self.get_state()

    def wait_while_input_ignored(self, max_frames=900):
        """During scripted scenes (e.g. Oak walking over) the game ignores every button."""
        for _ in range(max_frames // 6):
            self.wait_for_screen_to_settle()
            ignore = self.read_memory(JOY_IGNORE)
            all_ignored = ignore == 0xFF
            between_lines = ignore != 0 and not read_screen_text(self)
            if not (all_ignored or between_lines):
                break
            self.emulator.tick(6)

    def wait_for_screen_to_settle(self, max_frames=180):
        previous = self.screen_tiles()
        for _ in range(max_frames // 6):
            self.emulator.tick(6)
            current = self.screen_tiles()
            if current == previous:
                return
            previous = current

    def screen_tiles(self):
        return [self.read_memory(SCREEN + i) for i in range(SCREEN_SIZE)]

    def load(self, save_name):
        self.emulator.load_state(f"saves/{save_name}.state")
        self.emulator.tick(2)
        self.visited_maps = Counter()
        self.current_map = None
        return self.get_state()

    def save(self, save_name):
        self.emulator.save_state(f"saves/{save_name}.state")

    def read_memory(self, address):
        return self.emulator._pyboy.memory[address]
