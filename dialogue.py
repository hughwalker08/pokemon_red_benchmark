from screen_text import read_screen_text


def is_plain_dialogue(game, text):
    """Text on screen with no menu cursor: pressing A is the only way forward."""
    if not text or any("▶" in line for line in text):
        return False
    return not game.get_state()["battle"]["in_battle"]


def advance_dialogue(game, max_presses=80):
    """Press through plain dialogue, including scripted scenes. Returns (transcript lines, presses used)."""
    transcript = []
    presses = 0
    unchanged = 0
    while presses < max_presses:
        text = read_screen_text(game)
        if not text:
            game.emulator.tick(30)
            game.wait_while_input_ignored()
            text = read_screen_text(game)
        if not is_plain_dialogue(game, text):
            break
        for line in text:
            line = line.replace("▼", "").strip()
            if line and line not in transcript[-2:]:
                transcript.append(line)
        tiles_before = game.screen_tiles()
        game.do("b")  # B advances text like A, but can never start a new conversation
        presses += 1
        unchanged = unchanged + 1 if game.screen_tiles() == tiles_before else 0
        if unchanged >= 4:
            break
    return transcript, presses
