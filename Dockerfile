FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.14 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable --python /usr/local/bin/python

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/app/.venv/bin:$PATH"
RUN useradd --create-home --uid 10001 bot
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
USER bot
CMD ["zalo-bot", "run"]
