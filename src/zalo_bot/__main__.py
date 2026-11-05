"""CLI: run polling, check configuration/credentials, or explicitly remove a webhook."""

import argparse
import asyncio
import logging
import signal

from pydantic import ValidationError

from zalo_bot.client import ZaloAPIError, ZaloClient
from zalo_bot.config import Settings
from zalo_bot.polling import run_polling

logger = logging.getLogger(__name__)


async def run(command: str, settings: Settings) -> None:
    task = asyncio.current_task()
    assert task is not None
    loop = asyncio.get_running_loop()
    registered: list[signal.Signals] = []
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, task.cancel)
                registered.append(sig)
            except NotImplementedError:  # Windows: asyncio.run still handles Ctrl+C.
                pass
        async with ZaloClient(settings) as client:
            if command == "delete-webhook":
                await client.delete_webhook()
                logger.info("Webhook removed; long polling is available")
                return
            await client.get_me()
            info = await client.get_webhook_info()
            if info["url"]:
                raise RuntimeError("A webhook is active. Run 'zalo-bot delete-webhook' to switch.")
            logger.info("Credentials valid; no webhook configured")
            if command == "run":
                logger.info("Long polling started; press Ctrl+C to stop")
                await run_polling(client, settings)
    finally:
        for sig in registered:
            loop.remove_signal_handler(sig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Zalo Bot API long-polling application")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "check-config", "check-api", "delete-webhook"],
    )
    args = parser.parse_args()
    try:
        settings = Settings()
    except ValidationError:
        # ValidationError can render input values, including a plaintext environment token.
        parser.exit(2, "Invalid configuration. Check .env against .env.example and README.md.\n")
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    # HTTP request logs include the token in the URL, even at INFO level.
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    if args.command == "check-config":
        logger.info("Configuration valid (no network requests made)")
        return
    try:
        asyncio.run(run(args.command, settings))
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Bot stopped")
    except (ZaloAPIError, RuntimeError) as exc:
        logger.error("%s", exc)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
