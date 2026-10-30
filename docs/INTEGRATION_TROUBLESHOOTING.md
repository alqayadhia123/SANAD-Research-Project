# SANAD Integration Troubleshooting Runbook

**Scope:** local/research integration of PostgreSQL 16, Keycloak 26.4.2, and the Flask SANAD API.
**Safety:** synthetic data only. Never paste `.env`, passwords, client secrets, access tokens, or Authorization headers into logs or issues.
**Production status:** this runbook does not certify production readiness.

## 1. Validate Compose configuration

From the repository root:

```bash
docker version
docker compose version
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml config --quiet
```

If config validation fails, check that `transport_poc/.env` exists and contains every required variable. Do not commit that file.

## 2. Start and inspect services

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml up --build -d
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml ps --all
```

Inspect logs independently:

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml logs --tail=200 postgres-transport
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml logs --tail=200 keycloak-transport
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml logs --tail=200 driver-api
```

## 3. PostgreSQL checks

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml exec -T postgres-transport sh -lc 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml exec -T postgres-transport sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select version(), current_database(), current_user;"'
```

Expected: `pg_isready` reports accepting connections and the SQL query returns server/database/user metadata. If not, inspect the PostgreSQL logs, required environment variables, volume permissions, and whether the named volume contains an incompatible/old initialization state. Do not delete the volume until its data is known to be disposable.

## 4. Keycloak readiness and OIDC discovery

The Compose health check currently probes TCP port 9000, which proves only that the management listener accepts a connection. It does not by itself prove that the realm or OIDC endpoints are correctly configured.

From the API container:

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml exec -T driver-api python -c 'import json,urllib.request; u="http://keycloak-transport:8080/realms/master/.well-known/openid-configuration"; d=json.load(urllib.request.urlopen(u,timeout=5)); print({k:d.get(k) for k in ("issuer","token_endpoint","token_introspection_endpoint")})'
```

Expected: HTTP 200 and non-empty `issuer`, `token_endpoint`, and `token_introspection_endpoint`. The issuer used by API token validation must exactly match the issuer claim returned by introspection (after the API's trailing-slash normalization).

If discovery fails:
- inspect Keycloak startup logs and container health;
- confirm PostgreSQL is healthy and Keycloak database credentials match;
- confirm the container can resolve `postgres-transport`;
- confirm the configured HTTP port is 8080 and management health is enabled;
- distinguish TCP readiness from HTTP readiness.

## 5. Realm and client configuration

The integration workflow creates a disposable `sanad-lab` realm and a confidential service client `driver-wallet-api` for Client Credentials testing. Confirm:
- client is enabled and confidential;
- service accounts are enabled;
- client secret in the API environment matches the Keycloak client secret;
- access token includes audience `driver-wallet-api`;
- access token includes scope `wallet:read`;
- API issuer equals the realm's actual issuer.

Do not use Direct Access Grants/password grant as a substitute for driver authentication. Client Credentials proves service-to-service authorization only.

## 6. API checks

```bash
curl --fail --silent --show-error http://127.0.0.1:5001/health
```

Expected: HTTP 200 and `status=ok`. This is liveness only; it does not prove Keycloak connectivity or protected-route authorization.

The live CI assertions separately request:
- no bearer token -> 401;
- valid token without required scope -> 403;
- valid token with required scope and audience -> 200;
- invalid token -> 401.

If the API returns 503, inspect Keycloak reachability, introspection endpoint, confidential-client authentication, and API container logs. Fail-closed 503 during an identity-provider outage is expected behavior.

## 7. Safe reset and shutdown

Stop services while retaining the PostgreSQL volume:

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml down
```

Delete the volume only when intentionally discarding all local lab data:

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml down --volumes --remove-orphans
```

## 8. Evidence rules

For each run record exact commit SHA, workflow URL, job conclusion, assertions that actually executed, sanitized logs, and timestamps. A successful image build or `/health` response is not evidence of OIDC integration. A Client Credentials test is not evidence of driver Passkey/WebAuthn, account recovery, token/session revocation, or transaction-bound approval.
