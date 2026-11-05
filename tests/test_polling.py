import asyncio
from unittest.mock import AsyncMock

import pytest

from zalo_bot.client import ZaloAPIError
from zalo_bot.models import Update
from zalo_bot.polling import run_polling


async def test_backoff_reset_duplicates_and_handler_isolation(settings, event, monkeypatch, caplog):
    update = Update.model_validate(event)
    other = update.model_copy(deep=True)
    other.message.message_id = "message-2"
    sleeps = AsyncMock()
    monkeypatch.setattr("zalo_bot.polling.asyncio.sleep", sleeps)
    monkeypatch.setattr("zalo_bot.polling.random.uniform", lambda low, high: high)
    client = AsyncMock()
    client.get_update.side_effect = [
        ZaloAPIError(503, retryable=True),
        ZaloAPIError(429, retryable=True, retry_after=5),
        update,
        update,
        ZaloAPIError(retryable=True),
        other,
        other,
        asyncio.CancelledError(),
    ]
    handler = AsyncMock(side_effect=[None, ValueError("private user text"), None])
    with pytest.raises(asyncio.CancelledError):
        await run_polling(client, settings, handler=handler)
    assert handler.await_count == 3
    assert [call.args[0] for call in sleeps.await_args_list] == [1, 5, 0.1, 1]
    assert "ValueError" in caplog.text
    assert "private user text" not in caplog.text


async def test_permanent_error_stops_polling(settings):
    client = AsyncMock()
    client.get_update.side_effect = ZaloAPIError(401)
    with pytest.raises(ZaloAPIError):
        await run_polling(client, settings)
    assert client.get_update.await_count == 1


async def test_cancellation_interrupts_pending_poll(settings):
    entered = asyncio.Event()

    async def pending():
        entered.set()
        await asyncio.Event().wait()

    client = AsyncMock()
    client.get_update.side_effect = pending
    task = asyncio.create_task(run_polling(client, settings))
    await asyncio.wait_for(entered.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=1)
