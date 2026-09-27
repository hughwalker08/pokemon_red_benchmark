"""Map names by map number, following the pokered disassembly's map constants.

The harness's own table drifts out of line from map 47 onwards (e.g. it calls Viridian Forest
"Pewter Museum 1F"), so we use this instead. Maps not listed here are shown as "map N" rather
than risk a wrong name.
"""

MAP_NAMES = {
    0x00: "Pallet Town", 0x01: "Viridian City", 0x02: "Pewter City", 0x03: "Cerulean City",
    0x04: "Lavender Town", 0x05: "Vermilion City", 0x06: "Celadon City", 0x07: "Fuchsia City",
    0x08: "Cinnabar Island", 0x09: "Indigo Plateau", 0x0A: "Saffron City",
    0x0C: "Route 1", 0x0D: "Route 2", 0x0E: "Route 3", 0x0F: "Route 4", 0x10: "Route 5",
    0x11: "Route 6", 0x12: "Route 7", 0x13: "Route 8", 0x14: "Route 9", 0x15: "Route 10",
    0x16: "Route 11", 0x17: "Route 12", 0x18: "Route 13", 0x19: "Route 14", 0x1A: "Route 15",
    0x1B: "Route 16", 0x1C: "Route 17", 0x1D: "Route 18", 0x1E: "Route 19", 0x1F: "Route 20",
    0x20: "Route 21", 0x21: "Route 22", 0x22: "Route 23", 0x23: "Route 24", 0x24: "Route 25",
    0x25: "Red's House 1F", 0x26: "Red's House 2F", 0x27: "Blue's House", 0x28: "Oak's Lab",
    0x29: "Viridian Pokecenter", 0x2A: "Viridian Mart", 0x2B: "Viridian School House",
    0x2C: "Viridian Nickname House", 0x2D: "Viridian Gym", 0x2E: "Diglett's Cave (Route 2 entrance)",
    0x2F: "Viridian Forest North Gate", 0x30: "Route 2 Trade House", 0x31: "Route 2 Gate",
    0x32: "Viridian Forest South Gate", 0x33: "Viridian Forest", 0x34: "Pewter Museum 1F",
    0x35: "Pewter Museum 2F", 0x36: "Pewter Gym", 0x37: "Pewter Nidoran House", 0x38: "Pewter Mart",
    0x39: "Pewter Speech House", 0x3A: "Pewter Pokecenter", 0x3B: "Mt. Moon 1F", 0x3C: "Mt. Moon B1F",
    0x3D: "Mt. Moon B2F", 0x3E: "Cerulean Trashed House", 0x3F: "Cerulean Trade House",
    0x40: "Cerulean Pokecenter", 0x41: "Cerulean Gym", 0x42: "Bike Shop", 0x43: "Cerulean Mart",
    0x44: "Mt. Moon Pokecenter",
}


def map_name(map_id):
    return MAP_NAMES.get(map_id, f"map {map_id}")
