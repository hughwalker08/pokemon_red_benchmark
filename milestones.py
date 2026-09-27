"""Main-story milestones, in story order, from the start of the game up to the first badge."""


def visited(name):
    return lambda state, effect, game: name in game.visited_maps


MILESTONES = [
    ("left_house", visited("Pallet Town")),
    ("oak_stopped_you", lambda state, effect, game: "OAK: Hey! Wait!" in effect),
    ("got_starter", lambda state, effect, game: len(state["party"]) > 0),
    ("rival_battle", lambda state, effect, game: state["battle"]["type"] == "trainer" and state["map"]["map_name"] == "Oak's Lab"),
    ("reached_route_1", visited("Route 1")),
    ("reached_viridian_city", visited("Viridian City")),
    ("got_oaks_parcel", lambda state, effect, game: state["flags"]["has_oaks_parcel"]),
    ("got_pokedex", lambda state, effect, game: state["flags"]["has_pokedex"]),
    ("reached_route_2", visited("Route 2")),
    ("reached_viridian_forest", visited("Viridian Forest")),
    ("reached_pewter_city", visited("Pewter City")),
    ("entered_pewter_gym", visited("Pewter Gym")),
    ("boulder_badge", lambda state, effect, game: state["player"]["badge_count"] >= 1),
]


class MilestoneTracker:
    def __init__(self):
        self.reached = {}  # milestone name -> step it was first reached

    def update(self, step, state, effect, game):
        """Check every milestone not yet reached; return the names reached this step."""
        new = []
        for name, test in MILESTONES:
            if name not in self.reached and test(state, effect, game):
                self.reached[name] = step
                new.append(name)
        return new

    def score(self):
        return len(self.reached)
