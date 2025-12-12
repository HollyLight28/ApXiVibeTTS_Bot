import json

from app.web_search import brave_search


def test_brave_search_parses_results(monkeypatch):
    sample = {
        "web": {
            "results": [
                {"title": "Site A", "url": "https://a.example", "description": "Desc A"},
                {"title": "Site B", "url": "https://b.example", "description": "Desc B"},
            ]
        }
    }

    class FakeResp:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps(sample).encode("utf-8")

    def fake_urlopen(req, timeout=8):  # noqa: ARG001
        return FakeResp()

    monkeypatch.setenv("BRAVE_API_KEY", "X")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    results = brave_search("python", max_results=2)
    assert results and isinstance(results, list)
    assert results[0]["title"] == "Site A"
    assert results[0]["url"].startswith("https://")


def test_brave_search_no_key_returns_empty(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    assert brave_search("python") == []

