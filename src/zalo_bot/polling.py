"""Sequential long polling, bounded duplicate suppression, and transient-error backoff."""

import asyncio
import logging
import random
from collections import OrderedDict
from collections.abc import Awaitable, Callable

from zalo_bot.client import ZaloAPIError, ZaloClient
from zalo_bot.config import Settings
from zalo_bot.handlers import handle_update
from zalo_bot.models import Update

logger = logging.getLogger(__name__)
Handler = Callable[[ZaloClient, Update], Awaitable[None]]


async def run_polling(
    client: ZaloClient, settings: Settings, *, handler: Handler = handle_update
) -> None:
    delay = settings.retry_initial
    seen: OrderedDict[tuple[str, str, str], None] = OrderedDict()
    while True:
        try:
            update = await client.get_update()
        except ZaloAPIError as exc:
            if not exc.retryable:
                raise
            wait = max(random.uniform(delay / 2, delay), exc.retry_after)
            logger.warning("Polling failed (code=%s); retrying in %.1fs", exc.code, wait)
            await asyncio.sleep(wait)
            delay = min(delay * 2, settings.retry_max)
            continue
        delay = settings.retry_initial
        if update is None:
            # Also protect against an upstream that returns empty responses immediately.
            await asyncio.sleep(0.1)
            continue
        message = update.message
        key = (update.event_name, message.chat.id, message.message_id) if message else None
        if key is not None and key in seen:
            await asyncio.sleep(0.1)
            continue
        try:
            await handler(client, update)
        except Exception as exc:
            # Avoid exception text/tracebacks, which may contain tokens or user message bodies.
            logger.error("Update handler failed (%s); continuing", type(exc).__name__)
            continue
        if key is not None:
            seen[key] = None
            if len(seen) > 1000:
                seen.popitem(last=False)
