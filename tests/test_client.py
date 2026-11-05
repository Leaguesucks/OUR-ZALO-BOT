import json

import httpx
import pytest

from zalo_bot.client import ZaloAPIError, ZaloClient
from zalo_bot.handlers import handle_update


async def test_poll_to_reply_contract(settings, event):
    requests = []

    def respond(request):
        requests.append(request)
        if request.url.path.endswith("/getUpdates"):
            assert json.loads(request.content) == {"timeout": "30"}
            return httpx.Response(200, json={"ok": True, "result": event})
        assert request.url.path == "/bot123:test-token/sendMessage"
        assert json.loads(request.content) == {"chat_id": "chat-1", "text": "pong"}
        return httpx.Response(200, json={"ok": True, "result": {"message_id": "reply-1"}})

    async with ZaloClient(settings, transport=httpx.MockTransport(respond)) as client:
        update = await client.get_update()
        assert update is not None
        await handle_update(client, update)
    assert len(requests) == 2
    assert all(r.method == "POST" for r in requests)


@pytest.mark.parametrize("status", [200, 408])
async def test_poll_timeout_is_idle(settings, status):
    transport = httpx.MockTransport(
        lambda _: httpx.Response(status, json={"ok": False, "error_code": 408})
    )
    async with ZaloClient(settings, transport=transport) as client:
        assert await client.get_update() is None
        with pytest.raises(ZaloAPIError):
            await client.send_message("chat", "hello")


@pytest.mark.parametrize(
    ("status", "body", "code", "retryable"),
    [
        (401, {}, 401, False),
        (429, {}, 429, True),
        (503, {}, 503, True),
        (200, {"ok": False, "error_code": 401, "description": "123:test-token"}, 401, False),
        (200, {"ok": False, "error_code": 429}, 429, True),
        (200, {"ok": True, "result": []}, None, False),
        (200, {"ok": True}, None, False),
        (200, {"ok": "true"}, None, False),
        (200, [], None, False),
        (302, {}, 302, False),
    ],
)
async def test_api_errors_are_sanitized(settings, status, body, code, retryable):
    transport = httpx.MockTransport(lambda _: httpx.Response(status, json=body))
    async with ZaloClient(settings, transport=transport) as client:
        with pytest.raises(ZaloAPIError) as caught:
            await client.get_update()
    assert caught.value.code == code
    assert caught.value.retryable is retryable
    assert "test-token" not in str(caught.value)


async def test_network_failure_and_retry_after(settings):
    def fail(request):
        raise httpx.ReadTimeout(f"Secret URL: {request.url}", request=request)

    async with ZaloClient(settings, transport=httpx.MockTransport(fail)) as client:
        with pytest.raises(ZaloAPIError) as caught:
            await client.get_update()
    assert caught.value.retryable
    assert "test-token" not in str(caught.value)

    transport = httpx.MockTransport(lambda _: httpx.Response(429, headers={"Retry-After": "12"}))
    async with ZaloClient(settings, transport=transport) as client:
        with pytest.raises(ZaloAPIError) as caught:
            await client.get_update()
    assert caught.value.retry_after == 12


async def test_non_json_and_send_validation(settings):
    transport = httpx.MockTransport(lambda _: httpx.Response(200, text="not json"))
    async with ZaloClient(settings, transport=transport) as client:
        with pytest.raises(ZaloAPIError):
            await client.get_update()
        for text in ("", "a" * 2001):
            with pytest.raises(ValueError):
                await client.send_message("chat", text)


async def test_startup_api_methods(settings):
    methods = []

    def respond(request):
        method = request.url.path.rsplit("/", 1)[-1]
        methods.append(method)
        assert json.loads(request.content) == {}
        result = {"id": "bot-1"} if method == "getMe" else {"url": ""}
        return httpx.Response(200, json={"ok": True, "result": result})

    async with ZaloClient(settings, transport=httpx.MockTransport(respond)) as client:
        assert await client.get_me() == {"id": "bot-1"}
        assert await client.get_webhook_info() == {"url": ""}
        await client.delete_webhook()
    assert methods == ["getMe", "getWebhookInfo", "deleteWebhook"]
