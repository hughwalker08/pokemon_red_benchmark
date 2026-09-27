import json
from datetime import datetime
from pathlib import Path


class RunLog:
    def __init__(self, arm, settings):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.folder = Path("runs") / f"{timestamp}_{arm}"
        self.screenshots = self.folder / "screenshots"
        self.screenshots.mkdir(parents=True)
        self.steps_file = open(self.folder / "steps.jsonl", "w")
        self.settings = settings

    def log_step(self, step, record, screen):
        record = {"step": step, **record}
        self.steps_file.write(json.dumps(record) + "\n")
        self.steps_file.flush()
        screen.save(self.screenshots / f"{step:04}.png")

    def finish(self, summary):
        self.steps_file.close()
        with open(self.folder / "summary.json", "w") as f:
            json.dump({**self.settings, **summary}, f, indent=2)
