from app.history import add_assistant, add_user, clear, get_history_lines


def test_history_push_and_lines() -> None:
    ud: dict[str, object] = {}
    add_user(ud, "Привіт")
    add_assistant(ud, "Йо")
    add_user(ud, "Як справи?")
    lines = get_history_lines(ud, keep_last=2)
    assert any("assistant: Йо" in item for item in lines)
    assert any("user: Як справи?" in item for item in lines)


def test_history_clear() -> None:
    ud: dict[str, object] = {}
    add_user(ud, "A")
    add_assistant(ud, "B")
    clear(ud)
    lines = get_history_lines(ud)
    assert lines == []
