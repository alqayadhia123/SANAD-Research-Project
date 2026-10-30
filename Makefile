.PHONY: install test check compose-config

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

check: test

compose-config:
	docker compose --env-file env.transport -f transport_poc/docker-compose.transport.yaml config
