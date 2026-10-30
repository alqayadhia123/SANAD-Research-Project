PYTHON ?= python3
PIP := $(PYTHON) -m pip
COMPOSE := docker compose -f transport_poc/docker-compose.transport.yaml

.DEFAULT_GOAL := help
.PHONY: help install lock test test-unit test-integration lint type security audit-verify build up down logs health clean

help:
	@printf "%s\n" "SANAD developer commands" \
	  "  make install        Install project and development tools" \
	  "  make lock           Compile a dependency lock file with uv" \
	  "  make test           Run the complete pytest suite" \
	  "  make test-unit      Run tests excluding integration tests" \
	  "  make test-integration Run integration tests (requires Redis)" \
	  "  make lint           Run Ruff static checks" \
	  "  make type           Run mypy when configured" \
	  "  make security       Run Bandit and pip-audit" \
	  "  make audit-verify   Verify the P0 audit chain (if configured)" \
	  "  make build/up/down  Build or operate the local Compose lab" \
	  "  make health         Check the local API health endpoint" \
	  "  make clean          Remove Python build/test artifacts"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

lock:
	@command -v uv >/dev/null 2>&1 || $(PIP) install uv
	uv pip compile pyproject.toml -o requirements.lock --python-version 3.10

test:
	$(PYTHON) -m pytest -v --tb=short

test-unit:
	$(PYTHON) -m pytest -v -m "not integration"

test-integration:
	REDIS_URL=$${REDIS_URL:-redis://localhost:6379/15} $(PYTHON) -m pytest -v -m integration

lint:
	ruff check --select F transport_poc tests

type:
	@echo "mypy is not configured as a required P1 gate yet"

security:
	bandit -r transport_poc -ll
	pip-audit

audit-verify:
	@if test -f transport_poc/core/audit.py; then $(PYTHON) -c 'from transport_poc.core.audit import AuditLogger; r=AuditLogger().verify_chain(); print(r); raise SystemExit(0 if r["valid"] else 1)'; else echo "Audit verification unavailable: core/audit.py is not present in this branch"; exit 2; fi

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

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	rm -rf build dist *.egg-info .coverage htmlcov
