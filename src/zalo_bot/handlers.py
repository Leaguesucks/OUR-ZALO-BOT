"""Add application commands and business logic here."""

from zalo_bot.client import ZaloClient
from zalo_bot.models import Update

HELP_TEXT = "Hello! Commands: /start, /help, /ping. Send text and I will echo it."


async def handle_update(client: ZaloClient, update: Update) -> None:
    message = update.message
    if (
        update.event_name != "message.text.received"
        or message is None
        or not message.text
        or (message.sender is not None and message.sender.is_bot)
    ):
        return
    command = message.text.split(maxsplit=1)[0].lower() if message.text.strip() else ""
    if command in {"/start", "/help"}:
        reply = HELP_TEXT
    elif command == "/ping":
        reply = "pong"
    elif command.startswith("/"):
        reply = "Unknown command. Try /help."
    else:
        reply = message.text
    for start in range(0, len(reply), 2000):
        await client.send_message(message.chat.id, reply[start : start + 2000])
