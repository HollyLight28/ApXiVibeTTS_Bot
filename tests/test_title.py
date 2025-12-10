from app.title import infer_title


def test_infer_title_basic():
    t = "Це мій текст. Далі ще речення."
    assert infer_title(t) == "Це мій текст"


def test_infer_title_newline_split():
    t = "Заголовок\nа потім текст"
    assert infer_title(t) == "Заголовок"


def test_infer_title_long_truncation():
    t = "Слово " * 100
    assert len(infer_title(t)) <= 64


def test_infer_title_empty():
    assert infer_title("") == "TTS Audio"

