def state_to_text(state):
    player = state["player"]
    lines = []

    lines.append(f"Location: {state['map']['map_name']}")
    lines.append(f"Position: x={player['position']['x']}, y={player['position']['y']}, facing {player['facing']}")
    lines.append(f"Badges: {player['badge_count']}")

    if state["party"]:
        lines.append("Party:")
        for mon in state["party"]:
            lines.append(f"  {mon['nickname']} ({mon['species']}) Lv{mon['level']} HP {mon['hp']}/{mon['max_hp']} {mon['status']}")
    else:
        lines.append("Party: none yet")

    if state["bag"]:
        items = [f"{entry['item']} x{entry['quantity']}" for entry in state["bag"]]
        lines.append("Bag: " + ", ".join(items))

    if state["battle"]["in_battle"]:
        enemy = state["battle"].get("enemy") or {}
        lines.append(f"IN BATTLE vs {enemy.get('species')} Lv{enemy.get('level')} HP {enemy.get('hp')}/{enemy.get('max_hp')}")
    elif state["dialog"]["active"]:
        lines.append("A text box or menu is open.")
    else:
        lines.append("Map around you:")
        lines.append(state["collision"]["ascii"])

    return "\n".join(lines)
