# SANAD Remediation Status

## Changes committed in this branch

- Flask application factory and route registration baseline.
- Token introspection failures fail closed.
- Explicit audience validation; issuer is checked if returned by introspection.
- Required wallet scope enforced.
- Missing/invalid bearer token returns 401; insufficient scope returns 403.
- Authorization-server outage or missing introspection configuration returns 503.
- Synthetic-only wallet and route endpoints.
- Authenticator enrollment explicitly returns 501 until a real secure workflow exists.
- Browser-side hardcoded admin authentication and misleading WebAuthn/Vishing success states removed.
- Compose publishes API and Keycloak only on host loopback and uses an internal lab network.
- Mocked pytest suite and scenario matrix with NOT RUN / BLOCKED initial states.
- Environment template and ignore rules.

## Not implemented / not verified

- Live Keycloak realm/client provisioning and integration.
- Real WebAuthn registration and assertion verification.
- Independent OOB approval channel.
- Secure account recovery flow.
- Persistent application audit storage.
- End-to-end revocation timing.
- Browser automation or real authenticator tests.
- Docker image build and live Compose deployment.
- Production readiness.

## Validation status

Python syntax compilation is a static check only. Mocked tests, Docker, and live
Keycloak must be executed in a provisioned environment before any security
effectiveness claims are made. Do not report ASR/FPR values without actual
pre-registered experiments and evidence.

## Gate

`PRODUCTION_GATE=CLOSED`

A passing mocked unit test suite is necessary but insufficient for security validation.
