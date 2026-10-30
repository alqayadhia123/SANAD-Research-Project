# SANAD Free Development and Verification Workflow

**Status:** research/development workflow only. This document does not claim an always-on public deployment.

## 1. Operating model

Keep the project runnable without a paid cloud host:

- **Source of truth:** GitHub repository and pull requests.
- **Automated checks:** GitHub Actions (subject to the account's included minutes and storage quotas).
- **Local integration environment:** Docker Engine / Docker Desktop with Docker Compose.
- **Identity provider:** Keycloak container, using the local Compose lab configuration.
- **Database:** PostgreSQL container with a named local volume.
- **API:** Flask/Gunicorn container.
- **Evidence:** commit SHA, workflow run URL, test output, and sanitized logs.

This model supports development, repeatable tests, and research evidence collection. It does not guarantee a continuously available public endpoint.

## 2. One-time prerequisites

Install Docker Engine with the Compose plugin (or Docker Desktop) and Git. No paid Render resources are required for local development.

Clone the repository and select the active remediation branch:

```bash
git clone https://github.com/alqayadhia123/SANAD-Research-Project.git
cd SANAD-Research-Project
git switch fix/sanad-p0-security-baseline
```

## 3. Create local-only environment settings

Copy `transport_poc/.env.example` to `transport_poc/.env` locally, then replace every placeholder with a unique random value. Do not commit it, upload it as an artifact, or paste its values into issues or chat.

```bash
cp transport_poc/.env.example transport_poc/.env
```

Then edit `transport_poc/.env` and set the local values shown below:

```dotenv
POSTGRES_DB=sanad_local
POSTGRES_USER=sanad_local
POSTGRES_PASSWORD=replace-with-a-long-random-local-password
KC_BOOTSTRAP_ADMIN_USERNAME=sanad-local-admin
KC_BOOTSTRAP_ADMIN_PASSWORD=replace-with-a-different-long-random-password
OIDC_CLIENT_ID=driver-wallet-api
OIDC_CLIENT_SECRET=replace-with-a-local-client-secret
EXPECTED_AUDIENCE=driver-wallet-api
KEYCLOAK_HOST_PORT=8080
TRANSPORT_API_PORT=5001
```

Use unique random values for local use. The sample file is a template only; never reuse these credentials in a hosted environment. Confirm `transport_poc/.env` is ignored by Git before starting.

## 4. Start and stop the local stack

From the repository root:

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml config
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml up --build -d
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml ps
```

Local endpoints (bound to loopback by the Compose file):

- Keycloak: `http://127.0.0.1:8080`
- Flask API: `http://127.0.0.1:5001/health`

Compose waits for the Keycloak readiness health check before starting the API. The Keycloak container uses `start-dev` only for the isolated local lab. It is not a production configuration. Complete the Realm and confidential API client configuration in the local Keycloak admin console according to the deployment runbook before running authenticated integration tests.

Stop without deleting the PostgreSQL volume:

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml down
```

Delete the local database volume only when intentionally resetting all local lab state:

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml down --volumes
```

## 5. Run checks without cloud hosting

Python unit tests and synthetic-data validation:

```bash
python -m pip install -r transport_poc/driver_wallet_api/requirements-dev.txt
python transport_poc/scripts/validate_test_data.py
python -m pytest -q transport_poc/driver_wallet_api/tests
```

Container configuration and image validation:

```bash
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml config --quiet
docker build -t sanad-driver-api:local transport_poc/driver_wallet_api
```

The GitHub Actions workflows run automated checks on pushes and pull requests. GitHub's included Actions minutes and storage depend on the account and repository visibility; monitor usage and do not assume unlimited CI.

## 6. Safe collaboration and evidence

For every meaningful change:

1. Work on a feature branch; do not push experimental changes directly to `main`.
2. Open or update a pull request.
3. Require Python tests, synthetic-data validation, and container validation to pass.
4. Record the tested commit SHA and workflow run URL in the evidence register.
5. Keep test fixtures synthetic and logs sanitized.
6. Do not mark a scenario PASS unless its acceptance criteria were defined in advance and the test actually ran.
7. Keep `PRODUCTION_GATE=CLOSED` until the production security, operations, backup/restore, recovery, monitoring, and independent review requirements are met.

## 7. What is and is not free

| Capability | Zero-cost approach | Limitation |
|---|---|---|
| Source control | GitHub repository | Account and repository limits apply |
| CI tests | GitHub Actions included quota | Usage quotas and concurrency apply |
| API + Keycloak + PostgreSQL | Local Docker Compose | Runs only while the local machine is on |
| Persistent local lab data | Docker named volume | Local disk failure is not a backup |
| Public static documentation | GitHub Pages, if enabled | Does not host the Flask API or Keycloak |
| Public API available 24/7 | No dependable free-tier guarantee | Requires an always-on host and operational budget |

Free-tier cloud services may sleep, impose quotas, change terms, or be discontinued. They are not a substitute for an availability commitment. A tunnel from a personal computer is not a production hosting solution and should not expose the Keycloak admin console or database.

## 8. Render Blueprint warning

The current `render.yaml` describes paid PostgreSQL and web-service plans and reconciles the `sanad-demo` service to a paid Frankfurt service. Do not apply it for a zero-cost setup. Keep it as an optional deployment definition until an explicit budget is approved and the dashboard preview has been reviewed.

## 9. Research claim boundary

A local stack that starts, a passing unit suite, or a healthy API container proves only the corresponding technical checks. It does not establish phishing resistance, vishing resistance, account-recovery security, WebAuthn effectiveness, transaction authorization, or production availability. Those require separate threat-based tests and recorded evidence.
