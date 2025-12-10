from __future__ import annotations

import re


def split_text_into_chunks(text: str, max_chars: int = 7000) -> list[str]:
    # Розбиваємо текст на чанки по реченнях, щоб уникнути розривів усередині речень
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return []

    # Витягуємо речення, зберігаючи пунктуацію наприкінці
    sentences = re.findall(r".+?(?:[.!?](?:\s|$)|$)", cleaned, flags=re.S)

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in sentences:
        sent_stripped = sent.strip()
        if not sent_stripped:
            continue

        if current_len + len(sent_stripped) + (1 if current else 0) <= max_chars:
            current.append(sent_stripped)
            current_len += len(sent_stripped) + (1 if current_len > 0 else 0)
        else:
            if current:
                chunks.append(" ".join(current))
            # Якщо речення саме по собі довше за ліміт — розрізаємо всередині
            if len(sent_stripped) > max_chars:
                start = 0
                while start < len(sent_stripped):
                    end = min(start + max_chars, len(sent_stripped))
                    chunks.append(sent_stripped[start:end])
                    start = end
                current = []
                current_len = 0
            else:
                current = [sent_stripped]
                current_len = len(sent_stripped)

    if current:
        chunks.append(" ".join(current))

    return chunks

