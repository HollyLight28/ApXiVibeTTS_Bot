import os

import pytest

from app.tts_client import GeminiTTSClient


def test_tts_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        GeminiTTSClient()


def test_tts_client_initializes_with_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    c = GeminiTTSClient(model="gemini-2.5-flash-preview-tts")
    assert hasattr(c, "client")


def test_tts_generate_uses_audio_wav_and_content(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    c = GeminiTTSClient(model="gemini-2.5-flash-preview-tts")

    calls = {}

    class FakeResp:
        candidates = [type("C", (), {"content": type("CT", (), {"parts": [type("P", (), {"inline_data": type("ID", (), {"data": b"\x00\x00"})()})()]})()})()]

    def fake_generate_content(*args, **kwargs):  # noqa: ANN001
        calls["config"] = kwargs.get("config")
        calls["contents"] = kwargs.get("contents")
        return FakeResp()

    monkeypatch.setattr(c.client.models, "generate_content", fake_generate_content)

    data = c.generate_pcm("Hello", "Kore")
    assert isinstance(data, (bytes, bytearray))
    cfg = calls.get("config")
    assert getattr(cfg, "response_mime_type", None) == "audio/wav"
    cont = calls.get("contents")
    assert isinstance(cont, str) and cont == "Hello"
