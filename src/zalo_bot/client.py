"""Small async adapter for the official Zalo Bot API (not the separate OA API)."""

from types import TracebackType
from typing import Any

import httpx
from pydantic import ValidationError

from zalo_bot.config import Settings
from zalo_bot.models import Update

API_BASE = "https://bot-api.zaloplatforms.com"


class ZaloAPIError(Exception):
    """A sanitized error: never include token-bearing URLs or remote response bodies."""

    def __init__(
        self, code: int | None = None, *, retryable: bool = False, retry_after: float = 0
    ) -> None:
        super().__init__(f"Zalo API request failed (code={code})")
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after


class ZaloClient:
    def __init__(
        self, settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._poll_timeout = settings.poll_timeout
        self._http = httpx.AsyncClient(
            base_url=f"{API_BASE}/bot{settings.bot_token.get_secret_value()}/",
            timeout=httpx.Timeout(settings.request_timeout, connect=10),
            transport=transport,
            follow_redirects=False,
        )

    async def __aenter__(self) -> "ZaloClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._http.aclose()

    async def _call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        try:
            response = await self._http.post(method, json=payload or {})
        except httpx.TransportError:
            raise ZaloAPIError(retryable=True) from None

        if not response.is_success:
            try:
                retry_after = float(response.headers.get("Retry-After", "0"))
                retry_after = max(0.0, min(retry_after, 300.0))
            except ValueError:
                retry_after = 0
            raise ZaloAPIError(
                response.status_code,
                retryable=response.status_code == 429 or response.status_code >= 500,
                retry_after=retry_after,
            )
        try:
            body = response.json()
        except ValueError:
            raise ZaloAPIError() from None
        if not isinstance(body, dict) or not isinstance(body.get("ok"), bool):
            raise ZaloAPIError()
        if not body["ok"]:
            raw_code = body.get("error_code")
            code = raw_code if type(raw_code) is int else None
            raise ZaloAPIError(code, retryable=code == 429 or (code is not None and code >= 500))
        if "result" not in body:
            raise ZaloAPIError()
        return body["result"]

    async def get_me(self) -> dict[str, Any]:
        result = await self._call("getMe")
        if not isinstance(result, dict) or not isinstance(result.get("id"), str):
            raise ZaloAPIError()
        return result

    async def get_webhook_info(self) -> dict[str, Any]:
        result = await self._call("getWebhookInfo")
        if not isinstance(result, dict) or not isinstance(result.get("url"), str):
            raise ZaloAPIError()
        return result

    async def delete_webhook(self) -> None:
        await self._call("deleteWebhook")

    async def get_update(self) -> Update | None:
        try:
            result = await self._call("getUpdates", {"timeout": str(self._poll_timeout)})
        except ZaloAPIError as exc:
            if exc.code == 408:
                return None
            raise
        if result is None:
            return None
        try:
            return Update.model_validate(result)
        except ValidationError:
            raise ZaloAPIError() from None

    async def send_message(self, chat_id: str, text: str) -> None:
        if not chat_id or not 1 <= len(text) <= 2000:
            raise ValueError("A chat_id and 1–2000 characters of text are required")
        # Sends are intentionally not retried: a timeout can follow a successful delivery.
        await self._call("sendMessage", {"chat_id": chat_id, "text": text})
