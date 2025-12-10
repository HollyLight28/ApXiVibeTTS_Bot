from app.style import STYLE_PRESETS, build_style_instruction


def test_style_instruction_known_keys():
    for key in ["Neutral", "Slow", "Fast", "Emotional", "News", "Audiobook"]:
        instr = build_style_instruction(key)
        assert isinstance(instr, str)
        assert instr == STYLE_PRESETS[key]


def test_style_instruction_unknown_key():
    assert build_style_instruction("WTF") == ""


def test_style_instruction_none():
    assert build_style_instruction(None) == ""

