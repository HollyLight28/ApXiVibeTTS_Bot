from __future__ import annotations

STYLE_PRESETS: dict[str, str] = {
    "Neutral": "Говори нейтрально, природно, без зайвої експресії.",
    "Slow": "Говори повільно, чітко артикулюючи слова.",
    "Fast": "Говори швидко, енергійно, з динамікою.",
    "Emotional": "Говори емоційно, з теплим тоном і виразністю.",
    "News": "Говори у стилі новинного ведучого, рівномірно і впевнено.",
    "Audiobook": "Говори як диктор аудіокниги, плавно й виразно.",
}


def build_style_instruction(style_key: str | None) -> str:
    # Перетворює ключ стилю у коротку інструкцію для TTS
    if not style_key:
        return ""
    return STYLE_PRESETS.get(style_key, "")

