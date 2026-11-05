import os

import pytest

from zalo_bot.config import Settings


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    for name in os.environ:
        if name.startswith("ZALO_"):
            monkeypatch.delenv(name)


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, bot_token="123:test-token")


@pytest.fixture
def event() -> dict:
    return {
        "event_name": "message.text.received",
        "message": {
            "message_id": "message-1",
            "date": 1750316131602,
            "message_type": "CHAT_TEXT",
            "from": {"id": "user-1", "is_bot": False, "display_name": "Test"},
            "chat": {"id": "chat-1", "chat_type": "PRIVATE"},
            "text": "/ping",
        },
    }
