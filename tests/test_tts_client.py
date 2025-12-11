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
