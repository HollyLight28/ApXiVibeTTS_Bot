import pytest

from app.chunking import split_text_into_chunks


def test_single_chunk_when_under_limit():
    text = "Привіт. Це короткий текст для тесту. Він має кілька речень."
    chunks = split_text_into_chunks(text, max_chars=7000)
    assert len(chunks) == 1
    assert chunks[0].strip().startswith("Привіт")


def test_split_respects_sentence_boundaries():
    # Створюємо текст > 7000 символів із чіткими реченнями, щоб перевірити розбиття
    sentence = "Це речення доволі стандартне і повторюється. "
    long_text = (sentence * 400) + "Кінець."
    assert len(long_text) > 7000

    chunks = split_text_into_chunks(long_text, max_chars=7000)

    # Кожен чанк має бути <= 7000 символів
    assert all(len(c) <= 7000 for c in chunks)

    # Останній символ кожного чанку має бути або пробіл, або кінець рядка, або пунктуація
    assert all(c[-1] in ".!?\n " for c in chunks[:-1])


def test_handles_exact_boundary():
    # Рівно 7000 символів
    exact = "А" * 7000
    chunks = split_text_into_chunks(exact, max_chars=7000)
    assert len(chunks) == 1
    assert chunks[0] == exact


def test_no_empty_chunks():
    text = "Перше речення. Друге речення! Третє речення?"
    chunks = split_text_into_chunks(text, max_chars=20)
    assert all(len(c.strip()) > 0 for c in chunks)

