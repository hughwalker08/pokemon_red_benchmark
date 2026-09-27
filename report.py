"""Build a PDF comparing Arm A (Jev alone) and Arm B (Jev + GPT-6 Sol) from the run logs."""
import argparse
import json
import statistics
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402

from milestones import MILESTONES  # noqa: E402

COLOR = {"A": "#2a78d6", "B": "#eb6834"}  # reference palette slots 1 and 2 (validated light mode)
TEXT, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
NAMES = [name for name, _ in MILESTONES]
LABELS = {
    "left_house": "Left the house", "oak_stopped_you": "Oak stops you", "got_starter": "Got a starter",
    "rival_battle": "Rival battle", "reached_route_1": "Route 1", "reached_viridian_city": "Viridian City",
    "got_oaks_parcel": "Got Oak's Parcel", "got_pokedex": "Got the Pokédex", "reached_route_2": "Route 2",
    "reached_viridian_forest": "Viridian Forest", "reached_pewter_city": "Pewter City",
    "entered_pewter_gym": "Pewter Gym", "boulder_badge": "Boulder Badge",
}


def load_runs(tag, min_steps):
    runs = []
    for folder in sorted(Path("runs").glob(f"*_{tag}")):
        summary_path = folder / "summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text())
        if summary["steps_completed"] < min_steps:
            continue  # runs stopped by hand in the first few steps
        rows = [json.loads(line) for line in open(folder / "steps.jsonl")]
        effects = " ".join(r["effect"] for r in rows)
        last_party = next((line for line in rows[-1]["state_text"].split("\n") if line.startswith("  ") and " Lv" in line), "")
        battle_rows = [r for r in rows if "IN BATTLE" in r["state_text"]]
        summary.update({
            "folder": folder.name,
            "starter": last_party.split("(")[1].split(")")[0] if "(" in last_party else "-",
            "rival": "won" if "RED defeated BLUE" in effects else "lost" if "Am I great or what" in effects else "-",
            "blackouts": effects.count("RED blacked out"),
            "used_ember": effects.count("used EMBER"),
            "battle_steps": len(battle_rows),
        })
        runs.append(summary)
    return runs


def milestone_chart(runs, path):
    fig, ax = plt.subplots(figsize=(7.2, 5.2), dpi=200)
    for i, name in enumerate(NAMES):
        y = len(NAMES) - 1 - i
        ax.axhline(y, color=GRID, linewidth=0.6, zorder=0)
        for arm, offset in (("A", 0.16), ("B", -0.16)):
            steps = [r["milestones"][name] for r in runs if r["arm"] == arm and name in r["milestones"]]
            reached = len(steps)
            total = sum(1 for r in runs if r["arm"] == arm)
            if steps:
                ax.scatter(steps, [y + offset] * len(steps), s=22, color=COLOR[arm], alpha=0.55,
                           edgecolors="white", linewidths=0.8, zorder=3)
                ax.scatter([statistics.median(steps)], [y + offset], s=70, marker="D", color=COLOR[arm],
                           edgecolors="white", linewidths=1.2, zorder=4)
            ax.text(1.02, y + offset, f"{arm} {reached}/{total}", transform=ax.get_yaxis_transform(),
                    va="center", fontsize=7.5, color=COLOR[arm] if reached else MUTED)
    ax.set_xscale("log")
    ax.set_xlim(1.5, 2500)
    ax.set_xticks([2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000])
    ax.set_xticklabels(["2", "5", "10", "20", "50", "100", "200", "500", "1k", "2k"])
    ax.set_yticks(range(len(NAMES)))
    ax.set_yticklabels([LABELS[n] for n in reversed(NAMES)], fontsize=8.5, color=TEXT)
    ax.set_xlabel("Step first reached (log scale)", fontsize=8.5, color=MUTED)
    ax.tick_params(axis="x", labelsize=8, colors=MUTED)
    ax.tick_params(axis="y", length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.set_ylim(-0.6, len(NAMES) - 0.4)
    handles = [
        plt.Line2D([], [], marker="D", linestyle="", color=COLOR["A"], markersize=7, label="Arm A: Jev alone (median)"),
        plt.Line2D([], [], marker="D", linestyle="", color=COLOR["B"], markersize=7, label="Arm B: Jev + Sol (median)"),
        plt.Line2D([], [], marker="o", linestyle="", color=MUTED, alpha=0.55, markersize=5, label="one run"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3, frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def score_chart(runs, path):
    seeds = sorted({r["seed"] for r in runs})
    fig, ax = plt.subplots(figsize=(7.2, 2.6), dpi=200)
    width = 0.36
    for arm, shift in (("A", -width / 2), ("B", width / 2)):
        for j, seed in enumerate(seeds):
            run = next((r for r in runs if r["arm"] == arm and r["seed"] == seed), None)
            if run is None:
                continue
            x = j + shift
            ax.bar(x, run["milestone_score"], width=width, color=COLOR[arm], edgecolor="white", linewidth=1.5, zorder=3)
            ax.text(x, run["milestone_score"] + 0.25, str(run["milestone_score"]), ha="center", fontsize=8, color=TEXT)
    ax.set_xticks(range(len(seeds)))
    ax.set_xticklabels([f"seed {s}" for s in seeds], fontsize=8.5, color=TEXT)
    ax.set_ylim(0, len(NAMES) + 1)
    ax.set_yticks([0, 5, 10, 13])
    ax.set_ylabel("Milestones (of 13)", fontsize=8.5, color=MUTED)
    ax.tick_params(axis="y", labelsize=8, colors=MUTED, length=0)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.6, zorder=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR[a]) for a in ("A", "B")]
    ax.legend(handles, ["Arm A: Jev alone", "Arm B: Jev + Sol"], loc="lower center", bbox_to_anchor=(0.5, 1.0),
              ncol=2, frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def median_or_dash(values):
    return f"{statistics.median(values):g}" if values else "-"


def build_pdf(tag, clean_seeds, out_path, compare_tag=None):
    runs = load_runs(tag, min_steps=100)
    clean = [r for r in runs if r["seed"] in clean_seeds]
    caveat = [r for r in runs if r["seed"] not in clean_seeds]
    out_path.parent.mkdir(exist_ok=True)
    chart1 = out_path.with_name(f"{out_path.stem}_milestones.png")
    chart2 = out_path.with_name(f"{out_path.stem}_scores.png")
    milestone_chart(clean, chart1)
    score_chart(clean, chart2)

    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.5, leading=13.5, textColor=colors.HexColor(TEXT))
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=11, textColor=colors.HexColor(MUTED))
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=18, leading=22, alignment=0, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12.5, leading=16, spaceBefore=10, spaceAfter=4)

    def arm_stats(arm):
        rs = [r for r in clean if r["arm"] == arm]
        return {
            "n": len(rs),
            "avg": sum(r["milestone_score"] for r in rs) / len(rs),
            "cost": sum(r["total_cost"] for r in rs) / len(rs),
            "badges": sum(1 for r in rs if "boulder_badge" in r["milestones"]),
            "blackouts": sum(r["blackouts"] for r in rs) / len(rs),
        }

    a, b = arm_stats("A"), arm_stats("B")
    story = [
        Paragraph("Pokémon Red benchmark: Jev alone vs Jev + GPT-6 Sol", h1),
        Paragraph(f"{date.today():%d %B %Y} · runs tagged <b>{tag}</b> · sampling temperature "
                  f"<b>{clean[0]['temperature']:g}</b>", small),
        Spacer(1, 8),
        Paragraph(
            "Both arms play from the same new-game save with the same harness. Jev (TypeSafe, via OpenRouter) makes "
            "every decision in both arms. In Arm A its goal is fixed (“make progress in the main story toward the next "
            "badge”); in Arm B, GPT-6 Sol reads the game state every 15 steps and rewrites that goal. Each run is "
            "capped at 2,000 steps and ends early after 1,000 steps without a new milestone.", body),
        Spacer(1, 8),
    ]

    headline = Table([
        ["", "Arm A: Jev alone", "Arm B: Jev + Sol"],
        ["Average milestones (of 13)", f"{a['avg']:.2f}", f"{b['avg']:.2f}"],
        ["Runs that beat Brock (badge 1)", f"{a['badges']} of {a['n']}", f"{b['badges']} of {b['n']}"],
        ["Average blackouts per run", f"{a['blackouts']:.1f}", f"{b['blackouts']:.1f}"],
        ["Average cost per run", f"${a['cost']:.2f}", f"${b['cost']:.2f}"],
    ], colWidths=[62 * mm, 50 * mm, 50 * mm])
    headline.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9.5),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor(COLOR["A"])),
        ("TEXTCOLOR", (2, 0), (2, 0), colors.HexColor(COLOR["B"])),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(GRID)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f3")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [headline, Paragraph(f"Seeds {', '.join(map(str, clean_seeds))} ({a['n']} runs per arm).", small)]

    story += [Paragraph("How fast each arm reached each milestone", h2),
              Paragraph("Each small dot is one run; the diamond is the median. The column on the right counts how "
                        "many runs reached that milestone at all. The step axis is logarithmic so the early "
                        "milestones stay readable.", small),
              Image(str(chart1), width=172 * mm, height=124 * mm)]

    story += [PageBreak(), Paragraph("Milestones reached per run", h2), Image(str(chart2), width=172 * mm, height=62 * mm)]

    median_rows = [["Milestone", "Arm A median step", "Arm B median step", "Speed-up"]]
    for name in NAMES:
        sa = [r["milestones"][name] for r in clean if r["arm"] == "A" and name in r["milestones"]]
        sb = [r["milestones"][name] for r in clean if r["arm"] == "B" and name in r["milestones"]]
        speed = f"{statistics.median(sa) / statistics.median(sb):.1f}×" if sa and sb else "-"
        median_rows.append([LABELS[name], f"{median_or_dash(sa)} ({len(sa)}/{a['n']})", f"{median_or_dash(sb)} ({len(sb)}/{b['n']})", speed])
    medians = Table(median_rows, colWidths=[52 * mm, 42 * mm, 42 * mm, 26 * mm])
    medians.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8.5), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(GRID)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f3")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [Paragraph("Median step per milestone", h2),
              Paragraph("Median over the runs that reached it; brackets show how many runs did. Speed-up = Arm A "
                        "median ÷ Arm B median.", small), Spacer(1, 3), medians]

    run_rows = [["Arm", "Seed", "Steps", "Score", "Starter", "Rival", "Blackouts", "Ember uses", "Cost"]]
    for r in sorted(clean + caveat, key=lambda r: (r["arm"], r["seed"])):
        mark = "*" if r in caveat else ""
        run_rows.append([r["arm"], f"{r['seed']}{mark}", r["steps_completed"], r["milestone_score"], r["starter"],
                         r["rival"], r["blackouts"], r["used_ember"], f"${r['total_cost']:.3f}"])
    run_table = Table(run_rows, colWidths=[12 * mm, 14 * mm, 16 * mm, 15 * mm, 26 * mm, 16 * mm, 20 * mm, 22 * mm, 18 * mm])
    run_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8.5), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(GRID)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f3")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [Paragraph("Every run", h2), run_table]
    if caveat:
        story.append(Paragraph("* Seed 1 ran before a map-name fix: its “Viridian Forest” milestone was really the "
                               "forest gate, and Arm B’s “Pewter Gym” was really the museum’s second floor. It is "
                               "excluded from the charts and averages above.", small))
    if compare_tag:
        other = [r for r in load_runs(compare_tag, min_steps=100) if r["seed"] in clean_seeds]
        batches = sorted([(other[0]["temperature"], other), (clean[0]["temperature"], clean)], key=lambda b: b[0])
        (t_low, low), (t_high, high) = batches
        story += [PageBreak(), Paragraph("Does the temperature change the result?", h2),
                  Paragraph(f"The same seeds run at two sampling temperatures, T = {t_low:g} and T = {t_high:g}. "
                            "Median steps are over the runs that reached each milestone (brackets: how many did).",
                            small), Spacer(1, 4)]
        compare_rows = [["", f"Arm A, T={t_low:g}", f"Arm A, T={t_high:g}", f"Arm B, T={t_low:g}", f"Arm B, T={t_high:g}"]]

        def cell(batch, arm, name=None, key=None):
            rs = [r for r in batch if r["arm"] == arm]
            if key == "avg":
                return f"{sum(r['milestone_score'] for r in rs) / len(rs):.2f}"
            if key == "cost":
                return f"${sum(r['total_cost'] for r in rs) / len(rs):.2f}"
            if key == "badges":
                return f"{sum(1 for r in rs if 'boulder_badge' in r['milestones'])} of {len(rs)}"
            steps = [r["milestones"][name] for r in rs if name in r["milestones"]]
            return f"{median_or_dash(steps)} ({len(steps)}/{len(rs)})"

        order = [(arm, bt) for arm in "AB" for bt in (low, high)]
        compare_rows.append(["Average milestones"] + [cell(bt, arm, key="avg") for arm, bt in order])
        compare_rows.append(["Beat Brock"] + [cell(bt, arm, key="badges") for arm, bt in order])
        for name in NAMES:
            compare_rows.append([LABELS[name]] + [cell(bt, arm, name) for arm, bt in order])
        compare_rows.append(["Average cost per run"] + [cell(bt, arm, key="cost") for arm, bt in order])
        compare = Table(compare_rows, colWidths=[44 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm])
        compare.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), "Helvetica", 8.5), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5),
            ("FONT", (0, 1), (-1, 2), "Helvetica-Bold", 8.5),
            ("TEXTCOLOR", (1, 0), (2, 0), colors.HexColor(COLOR["A"])), ("TEXTCOLOR", (3, 0), (4, 0), colors.HexColor(COLOR["B"])),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(GRID)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f3")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(compare)
    return story, (a, b)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="v2")
    parser.add_argument("--clean-seeds", default="2,3,4,5")
    parser.add_argument("--out", default="reports/benchmark_report.pdf")
    parser.add_argument("--compare-tag", default="", help="another batch to compare against, e.g. v2")
    parser.add_argument("--notes", default="", help="optional file of extra paragraphs (one per blank-line block)")
    args = parser.parse_args()
    out = Path(args.out)
    story, _ = build_pdf(args.tag, [int(s) for s in args.clean_seeds.split(",")], out, args.compare_tag or None)
    if args.notes:
        styles = getSampleStyleSheet()
        body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.5, leading=13.5, spaceAfter=7)
        h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12.5, leading=16, spaceBefore=10, spaceAfter=4)
        story.append(PageBreak())
        for block in Path(args.notes).read_text().split("\n\n"):
            block = block.strip()
            if block.startswith("## "):
                story.append(Paragraph(block[3:], h2))
            elif block:
                story.append(Paragraph(block, body))
    SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=16 * mm, bottomMargin=16 * mm, title="Pokémon Red benchmark report").build(story)
    print("wrote", out)


if __name__ == "__main__":
    main()
