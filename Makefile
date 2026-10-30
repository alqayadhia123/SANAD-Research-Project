PYTHON ?= python3
COMPOSE := docker compose -f transport_poc/docker-compose.transport.yaml

.PHONY: help install test test-unit test-integration lint security build up down logs health
help:
	@printf "%s\n" "SANAD P1 commands" "  make install" "  make test" "  make test-integration" "  make build" "  make up" "  make down" "  make logs" "  make health"
install:
	$(PYTHON) -m pip install -e ".[dev]"
test:
	$(PYTHON) -m pytest -q
test-unit:
	$(PYTHON) -m pytest -q -m "not integration"
test-integration:
	REDIS_URL=$${REDIS_URL:-redis://localhost:6379/15} $(PYTHON) -m pytest -q -m integration
lint:
	ruff check --select F transport_poc
security:
	bandit -r transport_poc -ll
	pip-audit
build:
	$(COMPOSE) build
up:
	$(COMPOSE) up -d
down:
	$(COMPOSE) down
logs:
	$(COMPOSE) logs -f --tail=100
health:
	curl -fsS http://127.0.0.1:$${TRANSPORT_API_PORT:-5001}/health
