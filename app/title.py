from __future__ import annotations

import re

MAX_TITLE_LEN = 64


def infer_title(text: str) -> str:
    t = text.strip()
    if not t:
        return "TTS Audio"
    parts = re.split(r"[\.!?\n]+", t, maxsplit=1)
    first = (parts[0] if parts else t).strip()
    if not first:
        first = t
    first = re.sub(r"\s+", " ", first)
    title = first[:MAX_TITLE_LEN].strip()
    return title or "TTS Audio"

