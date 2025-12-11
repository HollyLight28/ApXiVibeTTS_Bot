import os

import pytest

from bot import get_webhook_config


def test_get_webhook_config_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    assert get_webhook_config() is None


def test_get_webhook_config_with_url_and_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBHOOK_URL", "https://example.com/hook")
    monkeypatch.setenv("PORT", "1234")
    url, port = get_webhook_config()  # type: ignore[misc]
    assert url == "https://example.com/hook"
    assert port == 1234

