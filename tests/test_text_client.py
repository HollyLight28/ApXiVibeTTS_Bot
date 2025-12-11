import pytest

from app.text_client import GeminiTextClient


def test_text_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        GeminiTextClient()


def test_generate_text_returns_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    c = GeminiTextClient(model="gemini-2.5-flash")

    class FakeResp:
        candidates = [type("C", (), {"content": type("CT", (), {"parts": [type("P", (), {"text": "hi"})()]})()})()]

    def fake_generate_content(*args, **kwargs):  # noqa: ANN001
        return FakeResp()

    monkeypatch.setattr(c.client.models, "generate_content", fake_generate_content)
    out = c.generate_text("Hello")
    assert out == "hi"

