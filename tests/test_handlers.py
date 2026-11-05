from unittest.mock import AsyncMock

import pytest

from zalo_bot.handlers import HELP_TEXT, handle_update
from zalo_bot.models import Update


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("/start", HELP_TEXT),
        ("/help", HELP_TEXT),
        ("/PING", "pong"),
        ("/unknown", "Unknown command. Try /help."),
        ("Xin chào", "Xin chào"),
    ],
)
async def test_commands_and_echo(event, text, expected):
    event["message"]["text"] = text
    client = AsyncMock()
    await handle_update(client, Update.model_validate(event))
    client.send_message.assert_awaited_once_with("chat-1", expected)


@pytest.mark.parametrize("variant", ["media", "no-message", "bot", "empty"])
async def test_ignored_events(event, variant):
    if variant == "media":
        event["event_name"] = "message.image.received"
    elif variant == "no-message":
        del event["message"]
    elif variant == "bot":
        event["message"]["from"]["is_bot"] = True
    else:
        event["message"]["text"] = ""
    client = AsyncMock()
    await handle_update(client, Update.model_validate(event))
    client.send_message.assert_not_awaited()


async def test_echo_splits_long_messages(event):
    event["message"]["text"] = "a" * 2001
    client = AsyncMock()
    await handle_update(client, Update.model_validate(event))
    assert [call.args[1] for call in client.send_message.await_args_list] == ["a" * 2000, "a"]
