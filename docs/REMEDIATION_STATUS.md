# SANAD Remediation Status

**Last reviewed:** 2026-10-30  
**Branch:** `fix/sanad-p0-security-baseline`  
**Gate:** `PRODUCTION_GATE=CLOSED`

## Implemented in the remediation branch

- Flask application factory and explicit route registration.
- Keycloak token introspection with fail-closed behavior on missing configuration, network errors, malformed responses, and inactive tokens.
- Exact configured issuer and expected audience checks; non-empty subject required.
- Case-insensitive Bearer scheme parsing and an 8 KiB bearer-token limit.
- Required wallet scope validation; malformed or insufficient scope claims are denied.
- Introspection response size capped at 64 KiB.
- Request body length is rejected with HTTP 413 before route logic when the declared size exceeds 16 KiB; Flask's own body limit remains enabled.
- Protected wallet and route endpoints; authenticator enrollment is authorization-protected and returns HTTP 501 until a genuine secure ceremony exists.
- Security response headers and `Cache-Control: no-store` on API responses.
- Synthetic-only wallet and route records; no real funds, customer records, or production transport integrations.
- Removal of hardcoded browser-side administrator credentials and misleading WebAuthn/Vishing success states.
- Compose network isolation and loopback-only published API/Keycloak ports.
- Python tests expanded from 25 to 30 test cases covering route authorization, request-size rejection, strict active-claim typing, and the introspection HTTP request contract. **All 30 tests passed** on commit `f57b0584dbd9329e1806e6d91293035a0e4e429f` in GitHub Actions run [#31](https://github.com/alqayadhia123/SANAD-Research-Project/actions/runs/41090476000).

## CI evidence and current rerun status

The previous branch head (`1bdfb9fd1e15c43610de7bc7242653b10c78ce8d`) had:
- Python workflow: success (25 tests and source compilation).
- Container workflow: success (Compose validation, API image build, and container `/health` smoke test).
- Live integration workflow: failure at the Keycloak readiness wait step. Realm provisioning and real token-introspection assertions were skipped.

The live integration workflow has now been changed to poll the Keycloak master-realm OIDC discovery document directly, validate required discovery fields, and emit service status/log diagnostics on timeout. This change is intended to improve readiness detection and diagnosis; it is **not yet considered fixed until a new workflow run passes**.

The revision `f57b0584dbd9329e1806e6d91293035a0e4e429f` also passed the container validation workflow [#13](https://github.com/alqayadhia123/SANAD-Research-Project/actions/runs/41090476019). The live integration workflow [#11](https://github.com/alqayadhia123/SANAD-Research-Project/actions/runs/41090475995) is still running; its result remains pending. The latest documentation-only commit is `2fec096240c0ebce76642f167b20d1f6de06543f`.

## Not implemented or not yet verified

- Live Keycloak realm/client provisioning and end-to-end introspection/authorization against the current branch revision.
- Real WebAuthn registration and assertion verification, including origin/RP ID checks, challenge lifecycle, and replay prevention.
- Independent out-of-band transaction approval.
- Secure account recovery and recovery-factor rotation.
- Persistent, tamper-evident application audit storage.
- Measured session/token revocation latency under realistic conditions.
- Browser automation and real authenticator interoperability.
- Production Keycloak configuration, TLS deployment, secrets management, backups, monitoring, and operational hardening.
- Independent penetration testing and a pre-registered attack-evaluation study.

## Research integrity rules

- CI success is software validation evidence, not proof of resistance to vishing, phishing, account takeover, or social engineering.
- A mocked introspection test is not equivalent to a live identity-provider integration test.
- A successful `/health` response proves process availability only.
- Keep scenario results as `NOT RUN`, `BLOCKED`, or explicit observed outcomes until linked to run artifacts/logs.
- Do not publish ASR, FPR, attack-success reduction, or security-effectiveness claims without a pre-registered protocol, defined denominators, repeated trials, and retained evidence.

## Local validation commands

From the repository root:

```bash
python -m pip install -r transport_poc/driver_wallet_api/requirements-dev.txt
python -m py_compile transport_poc/driver_wallet_api/app.py
cd transport_poc/driver_wallet_api
pytest -q
cd ../..
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml config --quiet
docker compose --env-file transport_poc/.env -f transport_poc/docker-compose.transport.yaml up --build -d
```

Use only disposable lab credentials and synthetic data. Never commit `transport_poc/.env` or production secrets.
