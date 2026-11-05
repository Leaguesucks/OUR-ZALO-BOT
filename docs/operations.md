# Operations

Run `make check` before changing application behavior. GitHub Actions repeats checks on
Python 3.11 and 3.14 and builds distributable packages. Tests require no secrets or live API.

For a live smoke test, set `ZALO_BOT_TOKEN`, run `make check-api`, start `make run`, and send
`/ping`, `/help`, and a normal text message from Zalo. Check that replies arrive, then stop
with Ctrl+C. No live API checks are performed by the test suite or CI.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Invalid configuration | Compare `.env` with `.env.example`; check required token and timeout ordering |
| 401/403 | Verify or regenerate the Bot Token in Zalo Bot Creator |
| Active webhook | Deliberately switch using `uv run --locked zalo-bot delete-webhook` |
| 429/5xx or transport failures | Check connectivity/quotas; polling backs off automatically |
| No replies | Confirm one running poller, correct bot, and text messages; inspect sanitized logs |
| Handler failure | Inspect the named exception class locally; avoid logging raw messages/tokens |

Token-bearing request URLs, response bodies, and user text are deliberately excluded from
application logs. HTTPX/HTTPCore logging is suppressed by the CLI because their URLs contain
tokens. When embedding the client, configure those loggers yourself. Never enable HTTP debug
traces against real credentials. Regenerate a token if it is exposed.

Keep a single replica. For supervision, run the container under your existing process manager
with restart-on-failure; do not start a second copy during deployment. No network healthcheck
endpoint is included. Monitor process exits and polling failures through your logging platform.

Zalo documents polling for local development and testing and recommends webhooks for production
to reduce missed events: [official guidance](https://docs.zaloplatforms.com/docs/BOT/apis/getUpdates).
This project follows the requested polling approach; assess event retention and add durable
processing before building critical workflows on top of it.
