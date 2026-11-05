import asyncio
from unittest.mock import AsyncMock

import pytest

from zalo_bot import __main__ as cli


async def test_active_webhook_requires_explicit_switch(settings, monkeypatch):
    client = AsyncMock()
    client.get_webhook_info.return_value = {"url": "https://example.com/webhook"}
    client.__aenter__.return_value = client
    monkeypatch.setattr(cli, "ZaloClient", lambda _: client)
    with pytest.raises(RuntimeError, match="webhook is active"):
        await cli.run("check-api", settings)
    client.delete_webhook.assert_not_awaited()
    client.__aexit__.assert_awaited_once()


async def test_explicit_delete_webhook(settings, monkeypatch):
    client = AsyncMock()
    client.__aenter__.return_value = client
    monkeypatch.setattr(cli, "ZaloClient", lambda _: client)
    await cli.run("delete-webhook", settings)
    client.delete_webhook.assert_awaited_once()
    client.get_me.assert_not_awaited()


async def test_cancellation_closes_client(settings, monkeypatch):
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.get_webhook_info.return_value = {"url": ""}
    monkeypatch.setattr(cli, "ZaloClient", lambda _: client)
    monkeypatch.setattr(cli, "run_polling", AsyncMock(side_effect=asyncio.CancelledError))
    with pytest.raises(asyncio.CancelledError):
        await cli.run("run", settings)
    client.__aexit__.assert_awaited_once()


def test_invalid_config_does_not_print_secret(monkeypatch, capsys):
    monkeypatch.setenv("ZALO_BOT_TOKEN", "do-not-print/secret")
    monkeypatch.setattr("sys.argv", ["zalo-bot", "check-config"])
    with pytest.raises(SystemExit) as caught:
        cli.main()
    assert caught.value.code == 2
    assert "do-not-print" not in capsys.readouterr().err


def test_check_config_is_offline(monkeypatch):
    monkeypatch.setenv("ZALO_BOT_TOKEN", "123:offline-token")
    monkeypatch.setattr("sys.argv", ["zalo-bot", "check-config"])
    run = AsyncMock()
    monkeypatch.setattr(cli, "run", run)
    cli.main()
    run.assert_not_called()
