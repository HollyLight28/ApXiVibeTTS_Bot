import json
from types import SimpleNamespace

from app.web_search import ddg_instant_answer


def test_ddg_instant_answer_parses_results(monkeypatch):
    sample = {
        "AbstractText": "Python — мова програмування.",
        "AbstractURL": "https://uk.wikipedia.org/wiki/Python",
        "RelatedTopics": [
            {"Text": "Python (програмування) - деталі", "FirstURL": "https://example.com/python"},
            {"Text": "Змії Python", "FirstURL": "https://example.com/snake"},
        ],
    }

    class FakeResp:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps(sample).encode("utf-8")

    def fake_urlopen(url, timeout=8):  # noqa: ARG001
        return FakeResp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    results = ddg_instant_answer("Python", max_results=3)
    assert results and isinstance(results, list)
    assert results[0]["title"] == "Abstract"
    assert "url" in results[0]
    assert any(r.get("url") for r in results)


def test_ddg_instant_answer_handles_error(monkeypatch):
    def fake_urlopen(url, timeout=8):  # noqa: ARG001
        raise RuntimeError("network error")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    results = ddg_instant_answer("Python")
    assert results == []

