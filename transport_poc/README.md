# SANAD Transport PoC — Remediation Baseline

## Scope and limitations

This is an isolated research baseline using synthetic data. The API uses Keycloak
Token Introspection and enforces an explicit audience and scope. It does **not**
implement WebAuthn registration/authentication, genuine out-of-band approval,
account recovery, persistent application audit logging, or a production wallet.
Do not report these capabilities as implemented or experimentally verified.

## 1. Configure

Copy `transport_poc/.env.example` to `transport_poc/.env` and replace every
placeholder with unique local secrets. Never commit `.env`.

Before API access can succeed, configure Keycloak:

1. Create realm `sanad-lab`.
2. Create a confidential OIDC client with client authentication enabled.
3. Set its client secret in `.env`.
4. Configure an Audience Mapper so introspection returns `aud` containing
   `driver-wallet-api`.
5. Ensure the issued access token includes `wallet:read`.
6. Use the internal issuer URL configured in `.env` from the API container.

The browser UI is only a thin API test client. It does not perform OIDC login
or WebAuthn. Obtain a disposable test access token through a separate trusted
test procedure; never paste production tokens into this page.

## 2. Validate and run Compose

From repository root:

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml config
docker compose --env-file .env -f transport_poc/docker-compose.transport.yaml up --build -d
docker compose --env-file .env -f transport_poc/docker-compose.transport.yaml ps
docker compose --env-file .env -f transport_poc/docker-compose.transport.yaml logs --no-color
```

Keycloak is published on host loopback port 8080 and the API on loopback port
5001. Compose waits for the Keycloak readiness health check before starting the
API. The Docker network is marked internal; this is network isolation, not a
universal guarantee against data exfiltration.

## 3. API smoke tests

```bash
curl -i http://127.0.0.1:5001/health
curl -i http://127.0.0.1:5001/api/driver/wallet
curl -i http://127.0.0.1:5001/api/driver/wallet \
  -H "Authorization: Bearer <DISPOSABLE_TEST_ACCESS_TOKEN>"
```

Expected behavior: health returns 200; missing bearer token returns 401;
unavailable/unconfigured introspection returns 503 (fail closed); inactive
token or wrong/missing audience returns 401; missing scope returns 403; valid
active token with correct audience and scope returns 200.

## 4. Automated tests

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r transport_poc/driver_wallet_api/requirements-dev.txt
pytest -q transport_poc/driver_wallet_api/tests
```

These are mocked unit tests. Passing them does not prove live Keycloak
integration, WebAuthn security, revocation propagation, or deployment correctness.

## 5. Evidence discipline

The CSV scenario matrix starts with `NOT RUN` or `BLOCKED`. Change a row only
after recording raw request/response evidence, software versions, timestamp,
commit SHA, and a predefined acceptance criterion. Never mark a scenario PASS
without reproducible evidence.
