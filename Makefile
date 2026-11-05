.PHONY: setup run test check format check-config check-api build

setup:
	bash scripts/bootstrap.sh

run:
	bash scripts/run.sh run

test:
	bash scripts/test.sh

check:
	bash scripts/check.sh

format:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .

check-config:
	bash scripts/run.sh check-config

check-api:
	bash scripts/run.sh check-api

build:
	uv build
