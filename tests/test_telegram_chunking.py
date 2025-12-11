from app.chunking import split_text_into_chunks


def test_chunking_respects_telegram_limit() -> None:
    text = "A" * 12000
    parts = split_text_into_chunks(text, max_chars=3800)
    assert parts and all(len(p) <= 3800 for p in parts)

