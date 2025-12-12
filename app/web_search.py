from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


def ddg_instant_answer(query: str, max_results: int = 5) -> list[dict[str, str]]:
    q = urllib.parse.quote(query)
    url = f"https://api.duckduckgo.com/?q={q}&format=json&no_redirect=1&no_html=1"
    scheme = urllib.parse.urlsplit(url).scheme
    if scheme not in ("https", "http"):
        return []
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    results: list[dict[str, str]] = []
    abstract = data.get("AbstractText") or data.get("Abstract")
    abs_url = data.get("AbstractURL") or ""
    if abstract:
        results.append({"title": "Abstract", "text": abstract, "url": abs_url})
    related = data.get("RelatedTopics") or []
    for item in related:
        t = item.get("Text") or ""
        u = item.get("FirstURL") or ""
        if t and u:
            results.append({"title": t.split(" - ")[0], "text": t, "url": u})
        if len(results) >= max_results:
            break
    return results


def brave_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    key = os.environ.get("BRAVE_API_KEY") or os.environ.get("BRAVE_SEARCH_API_KEY")
    if not key:
        return []
    q = urllib.parse.quote(query)
    url = f"https://api.search.brave.com/res/v1/web/search?q={q}"
    req = urllib.request.Request(url, headers={"X-Subscription-Token": key})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    items = []
    web = data.get("web") or {}
    results = web.get("results") or []
    for r in results[:max_results]:
        title = r.get("title") or ""
        url = r.get("url") or ""
        text = r.get("description") or ""
        if url:
            items.append({"title": title, "url": url, "text": text})
    return items
