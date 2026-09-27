import argparse
import json
from pathlib import Path

from milestones import MILESTONES


def load_summaries(tag):
    summaries = []
    for path in sorted(Path("runs").glob("*/summary.json")):
        summary = json.loads(path.read_text())
        if summary.get("tag") == tag:
            summaries.append(summary)
    return summaries


def main(tag):
    summaries = load_summaries(tag)
    if not summaries:
        print(f"No runs found with tag '{tag}'.")
        return

    names = [name for name, _ in MILESTONES]
    print(f"Runs tagged '{tag}' - step at which each milestone was first reached ('-' = never)\n")
    header = f"{'arm':>3} {'seed':>4} {'steps':>5} {'score':>5} {'cost':>7}  " + " ".join(f"{i + 1:>4}" for i in range(len(names)))
    print(header)
    for s in sorted(summaries, key=lambda s: (s["arm"], s["seed"])):
        cells = " ".join(f"{s['milestones'].get(name, '-'):>4}" for name in names)
        print(f"{s['arm']:>3} {s['seed']:>4} {s['steps_completed']:>5} {s['milestone_score']:>5} ${s['total_cost']:>6.3f}  {cells}")

    print("\nMilestone key:")
    for i, name in enumerate(names):
        print(f"  {i + 1:>2}. {name}")

    print("\nAverages:")
    for arm in sorted({s["arm"] for s in summaries}):
        runs = [s for s in summaries if s["arm"] == arm]
        average_score = sum(s["milestone_score"] for s in runs) / len(runs)
        total_cost = sum(s["total_cost"] for s in runs)
        print(f"  Arm {arm}: {len(runs)} runs, average {average_score:.1f} milestones, total cost ${total_cost:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="v2")
    main(parser.parse_args().tag)
