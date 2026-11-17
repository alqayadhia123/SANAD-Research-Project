# SANAD Security Patch — 2026-11-17

Repository: https://github.com/alqayadhia123/SANAD-Research-Project
Working branch: `fix/remove-demo-mode-bypass-20261117`
Scope: `transport_poc/driver_wallet_api` and transport lab configuration.

## Findings addressed

1. `DEMO_MODE=true` previously returned a synthetic driver identity before checking the Authorization header or validating an access token with Keycloak.
2. The Render blueprint declared `REQUIRED_WALLET_SCOPE=wallet:read`, but the API did not enforce the scope before returning wallet data. A valid token for the API audience could therefore reach the wallet route without the intended fine-grained permission.

## Patch

- Removed the `DEMO_MODE` authentication bypass. Bearer-token validation and Keycloak introspection remain mandatory.
- Preserved fail-closed behavior: missing bearer token returns HTTP 401; introspection configuration or availability failures return HTTP 503; inactive or invalid issuer/audience claims are denied.
- Enforced `wallet:read` on `GET /api/driver/wallet` and `route:read` on `GET /api/driver/route`; missing permissions return HTTP 403.
- Passed both scope settings through Docker Compose.
- Converted `env.transport.example` into a plain sourceable environment file and added both scope variables.
- Kept authenticator enrollment disabled with HTTP 501 until a complete WebAuthn ceremony validates challenge, origin, RP ID, attestation, and replay protections.

## Regression tests

File: `transport_poc/driver_wallet_api/tests/test_auth_fail_closed.py`

GitHub Actions ran the suite on Python 3.10.22. Result: **11 tests passed** (`Ran 11 tests ... OK`). Coverage includes:
- No bearer token and oversized bearer token.
- `DEMO_MODE=true` does not bypass authentication.
- Missing introspection configuration and inactive tokens.
- Missing audience and wrong issuer.
- Wallet and route scope denial when permissions are missing.
- Successful synthetic wallet and route reads when the corresponding scope is present.

Workflow: `.github/workflows/sanad-auth-tests.yml`.

## Verification limits

- Automated unit/regression tests passed in GitHub Actions.
- No live Keycloak integration test, Docker Compose validation/build, Render deployment, browser WebAuthn test, or production security certification was performed.
- Render issuer/realm configuration remains a deployment blocker; see `DEPLOYMENT_READINESS_2026-11-17.md`.

## Follow-up work

- Align the actual Keycloak issuer and realm with the deployment environment and verify real introspection claims/scopes.
- Replace Keycloak `start-dev` with a production-hardened configuration before any production use.
- Implement WebAuthn registration and authentication end-to-end before enabling authenticator enrollment.
- Review CSP and remove inline script/style allowances by moving assets to static files or using nonce/hash policies.
- Add durable audit events and verify role/scope design against the research scenarios.
