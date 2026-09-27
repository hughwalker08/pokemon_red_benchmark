from collections import deque


def describe_effect(before, after, text_before, text_after):
    if after["map"]["map_name"] != before["map"]["map_name"]:
        return f"entered {after['map']['map_name']}"
    if after["player"]["position"] != before["player"]["position"]:
        position = after["player"]["position"]
        return f"moved to ({position['x']},{position['y']})"
    if after["player"]["facing"] != before["player"]["facing"]:
        return f"turned to face {after['player']['facing']}"
    if text_after != text_before:
        if not text_after:
            return "text box closed"
        words = " ".join(line.strip() for line in text_after)
        return f'text: "{words[:80]}"'
    return "nothing changed"


class History:
    def __init__(self, length=10):
        self.steps = deque(maxlen=length)
        self.unchanged_count = 0

    def record(self, button, effect):
        self.steps.append(f"{button} -> {effect}")
        if effect == "nothing changed":
            self.unchanged_count += 1
        else:
            self.unchanged_count = 0

    def to_text(self):
        if not self.steps:
            return "Recent steps: none yet"
        lines = ["Recent steps (oldest first):"]
        lines.extend(f"  {step}" for step in self.steps)
        if self.unchanged_count:
            lines.append(f"Nothing has changed for the last {self.unchanged_count} steps.")
        return "\n".join(lines)
