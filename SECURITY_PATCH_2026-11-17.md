# SANAD Security Patch — 2026-11-17

Repository: https://github.com/alqayadhia123/SANAD-Research-Project
Working branch: `fix/remove-demo-mode-bypass-20261117`
Scope: `transport_poc/driver_wallet_api`

## Finding addressed

The API contained a `DEMO_MODE=true` branch in `authorized_subject()` that returned a synthetic driver identity before checking the Authorization header or validating an access token with Keycloak. This bypass contradicted the fail-closed authentication design documented in the earlier repair log.

## Patch

- Removed the `DEMO_MODE` authentication bypass.
- Kept bearer-token validation and Keycloak introspection as the only authorization path for protected wallet and route endpoints.
- Preserved fail-closed behavior: missing bearer token returns HTTP 401; introspection configuration or availability failures return HTTP 503; inactive or invalid claims are denied.
- Kept authenticator enrollment disabled with HTTP 501 until a complete WebAuthn registration flow validates challenge, origin, RP ID, attestation, and replay protections.

## Regression tests added

File: `transport_poc/driver_wallet_api/tests/test_auth_fail_closed.py`

The tests set `DEMO_MODE=true` deliberately and verify:
1. A missing bearer token is still rejected with HTTP 401.
2. A bearer token cannot bypass missing Keycloak introspection configuration (HTTP 503).
3. The route endpoint also rejects requests without authentication (HTTP 401).

Run from `transport_poc/driver_wallet_api`:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Verification limits

The patch and regression-test source were committed to the working branch through GitHub. The test suite was not executed in a local or CI runtime during this change. No Docker build, Keycloak integration test, deployment, or production security certification is claimed.

## Follow-up work

- Add CI to execute the regression tests on every pull request.
- Validate issuer, audience, expiry, and other required token claims against the actual Keycloak configuration.
- Implement WebAuthn registration and authentication end-to-end before enabling authenticator enrollment.
- Review CSP and remove inline script allowances by moving the UI script to a static asset or using a nonce/hash strategy.
