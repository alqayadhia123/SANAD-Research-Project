# SANAD Deployment Readiness Review — 2026-11-17

Repository: https://github.com/alqayadhia123/SANAD-Research-Project
Working branch: `fix/remove-demo-mode-bypass-20261117`
Classification: research proof of concept; deployment is not approved by this review.

## Confirmed configuration blockers

1. `render.yaml` defines the `sanad-demo` web service but does not define a Keycloak service. Its `KEYCLOAK_ISSUER` currently points to `http://keycloak-transport:8080/realms/sanad-lab`, which is the Docker Compose service hostname and is not established by the Render blueprint. Unless a separate reachable Keycloak service and private-network route are configured outside this repository, the Render API cannot introspect tokens at that address.
2. The Render issuer names realm `sanad-lab`, while `env.transport.example` and the API default use `riyadh-transport-lab`. The realm names and issuer URLs must be made consistent with the actual Keycloak realm before integration testing.
3. The Compose Keycloak service uses `start-dev`; this is suitable only for an isolated development lab, not a production deployment.
4. The API now requires `wallet:read` for wallet reads and `route:read` for route reads. Keycloak must issue these scopes in the introspection response. A client/audience match alone is not sufficient.
5. WebAuthn authenticator enrollment remains intentionally unavailable (HTTP 501). There is no complete registration or authentication ceremony in this repository branch.
6. The current Content-Security-Policy still permits inline scripts and styles. The UI should move JavaScript/CSS to static assets or use a nonce/hash policy before a production security review.
7. Wallet and route responses remain synthetic research data. No real balance, payment, dispatch, or financial transaction is connected.

## Changes in this patch

- Enforce `wallet:read` on `GET /api/driver/wallet`.
- Enforce `route:read` on `GET /api/driver/route`.
- Pass both scope settings through Docker Compose.
- Convert `env.transport.example` into a valid sourceable environment file and document both scope variables.

## Required validation before deployment

- Select and provision the actual Keycloak host and realm; do not assume Docker Compose service names resolve on Render.
- Configure the confidential client, audience, and scope mappers so introspection returns the expected `aud`, `iss`, and `scope` claims.
- Run live tests with a valid token, expired token, wrong issuer, wrong audience, missing wallet scope, and missing route scope.
- Replace `start-dev` with a production-hardened Keycloak deployment and HTTPS.
- Complete WebAuthn registration/authentication and UI accessibility checks before advertising Passkey support.
- Remove inline CSP allowances and add durable audit events before any real user or operational data is introduced.

No Render configuration, hosted service, secret, paid resource, or deployment was changed by this review.
