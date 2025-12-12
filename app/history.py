KEY = "chat_history"
 
def _list(user_data: dict[str, object]) -> list[dict[str, str]]:
    hist = user_data.get(KEY)
    if not isinstance(hist, list):
        hist = []
        user_data[KEY] = hist
    return hist


def add_user(user_data: dict[str, object], text: str, max_items: int = 24) -> None:
    hist = _list(user_data)
    hist.append({"role": "user", "text": text})
    while len(hist) > max_items:
        hist.pop(0)


def add_assistant(user_data: dict[str, object], text: str, max_items: int = 24) -> None:
    hist = _list(user_data)
    hist.append({"role": "assistant", "text": text})
    while len(hist) > max_items:
        hist.pop(0)


def get_history_lines(user_data: dict[str, object], keep_last: int = 10, summary_chars: int = 2000) -> list[str]:
    hist = _list(user_data)
    lines: list[str] = []
    if len(hist) > keep_last:
        older = hist[: len(hist) - keep_last]
        summary = []
        for m in older:
            summary.append(f"{m.get('role', 'user')}: {m.get('text', '')}")
        s = "\n".join(summary)
        if len(s) > summary_chars:
            s = s[: summary_chars] + " …"
        lines.append("Summary: " + s)
    tail = hist[-keep_last:]
    for m in tail:
        lines.append(f"{m.get('role', 'user')}: {m.get('text', '')}")
    return lines


def clear(user_data: dict[str, object]) -> None:
    user_data[KEY] = []
