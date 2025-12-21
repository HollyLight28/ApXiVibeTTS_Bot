import pytest

from app.groq_text_client import GroqTextClient


def test_groq_text_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        GroqTextClient()


def test_generate_text_returns_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "dummy-key")
    c = GroqTextClient(model="llama-3.3-70b-versatile")

    class FakeMessage:
        content = "привіт"

    class FakeChoice:
        message = FakeMessage()

    class FakeResp:
        choices = [FakeChoice()]

    def fake_create(*args, **kwargs):  # noqa: ANN001
        return FakeResp()

    monkeypatch.setattr(c.client.chat.completions, "create", fake_create)
    out = c.generate_text("Hello")
    assert out == "привіт"
