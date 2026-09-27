from pokemon_agent.collision import build_collision_grid, render_ascii_map
from pokemon_agent.emulator import create_emulator
from pokemon_agent.memory.red import PokemonRedReader
from pokemon_agent.state.builder import build_game_state
from pyboy import PyBoy

ROM_PATH = "roms/pokemon_red.gb"
BUTTONS = ["up", "down", "left", "right", "a", "b", "start", "select"]
MAP_ID = 0xD35E  # which map you're on; when it changes, the screen fades and input is ignored


class Game:
    def __init__(self, watch=False):
        self.emulator = create_emulator(ROM_PATH)
        if watch:
            self.emulator._pyboy.stop(save=False)
            self.emulator._pyboy = PyBoy(ROM_PATH, window="SDL2")
        self.reader = PokemonRedReader(self.emulator)
        self.visited_maps = set()

    def get_state(self):
        state = build_game_state(self.reader)
        self.visited_maps.add(state["map"]["map_name"])
        if not state["battle"]["in_battle"]:
            collision = build_collision_grid(self.emulator)
            collision["ascii"] = render_ascii_map(collision, legend=True)
            state["collision"] = collision
        return state

    def do(self, button):
        if button not in BUTTONS:
            raise ValueError(f"Unknown button: {button}")
        map_before = self.read_memory(MAP_ID)
        self.emulator.press(button, 8)
        self.emulator.tick(12)
        if self.read_memory(MAP_ID) != map_before:
            self.emulator.tick(120)
        return self.get_state()

    def load(self, save_name):
        self.emulator.load_state(f"saves/{save_name}.state")
        self.emulator.tick(2)
        self.visited_maps = set()
        return self.get_state()

    def save(self, save_name):
        self.emulator.save_state(f"saves/{save_name}.state")

    def read_memory(self, address):
        return self.emulator._pyboy.memory[address]
