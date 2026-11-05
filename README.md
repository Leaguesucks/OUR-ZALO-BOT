
# OUR Zalo Bot

Python 3.11+ starter for the **Zalo Bot API**, receiving events through long polling.
Includes `/start`, `/help`, `/ping`, and a text echo handler to verify the complete flow.

## Quick start

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Create a bot through Zalo Bot Manager → Zalo Bot Creator and obtain its Bot Token
   ([official instructions](https://docs.zaloplatforms.com/docs/BOT/create_bot)).
3. From this directory, run:

   ```bash
   make setup
   # Edit .env and set ZALO_BOT_TOKEN to your Bot Token.
   make check-config
   make check-api
   make run
   ```

Send `/ping` to your bot in Zalo; it should reply `pong`. Stop with Ctrl+C or SIGTERM.
Environment variables override `.env`; never commit your real token. This uses the Bot API,
which is separate from Zalo Official Account APIs and personal-account automation.

If a webhook is already configured, startup reports it. To switch this bot to polling explicitly:

```bash
uv run --locked zalo-bot delete-webhook
make run
```

Only run **one polling process per bot token**. No public server, inbound port, database,
or webhook endpoint is needed. Outbound HTTPS access is required.

## Development commands

| Command | Purpose |
| --- | --- |
| `make setup` | Install locked runtime/dev dependencies; create `.env` if absent |
| `make run` | Start the polling bot |
| `make test` | Run offline tests using mocked HTTP; no token needed |
| `bash scripts/test.sh -k polling` | Run selected tests |
| `make check` | Check formatting, lint, types, and tests with coverage |
| `make format` | Apply formatting and automatic lint fixes |
| `make check-config` | Validate local settings without network access |
| `make check-api` | Check credentials and webhook status; sends no chat messages |
| `make build` | Build wheel and source distribution |

Scripts work from any directory. Without Make, invoke `bash scripts/bootstrap.sh`,
`bash scripts/run.sh`, `bash scripts/test.sh`, or `bash scripts/check.sh` directly.
The installed CLI also supports `python -m zalo_bot`.

## Project layout

```text
src/zalo_bot/
  __main__.py       CLI, startup checks, shutdown, and client lifecycle
  config.py         Validated environment settings
  client.py         HTTP transport and sanitized API errors
  models.py         Minimal event/message models
  polling.py        Sequential polling, backoff, and duplicate suppression
  handlers.py       Example commands; add your business logic here
tests/             Offline API contract, handler, polling, config, and CLI tests
scripts/           Setup, run, test, and verification automation
docs/              Architecture and operational notes
.github/workflows/  CI for Python 3.11 and 3.14
```

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `ZALO_BOT_TOKEN` | Required | Token issued by Zalo Bot Creator |
| `ZALO_POLL_TIMEOUT` | `30` | Server-side wait in seconds; scaffold accepts 1–60 |
| `ZALO_REQUEST_TIMEOUT` | `40` | HTTP timeout; must exceed the polling wait |
| `ZALO_RETRY_INITIAL` | `1` | Initial transient polling retry delay in seconds |
| `ZALO_RETRY_MAX` | `30` | Maximum exponential backoff, up to 300 seconds |
| `ZALO_LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR, or CRITICAL |

`uv.lock` fixes dependency versions. Use `uv lock --upgrade` when intentionally updating,
then run `make check`. Python 3.11 is selected by `.python-version`; use
`uv sync --python 3.14 --locked --group dev` to try a newer interpreter.

## Container

```bash
docker build -t our-zalo-bot .
docker run --rm --env-file .env --init --name our-zalo-bot our-zalo-bot
```

The image runs as a non-root user; secrets are supplied at runtime. The local `.env`
is excluded from the build context. Container builds, local development, and CI use
the exact versions in `uv.lock`.

See [architecture](docs/architecture.md) and [operations](docs/operations.md) before
adding durable business workflows.
