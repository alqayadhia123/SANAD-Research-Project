# SANAD browser login and encrypted admin datasets

This branch adds a research-lab browser sign-in flow and an admin-only synthetic dataset upload API.

## Browser token issuance
- The browser uses Keycloak OIDC Authorization Code + PKCE (S256).
- Configure a **public** Keycloak client named by `PUBLIC_OIDC_CLIENT_ID`, with Standard Flow enabled, PKCE method S256 required, and exact redirect URI `https://YOUR_HOST/`.
- Configure allowed web origin to the exact deployment origin.
- Add `openid`, `profile`, and `wallet:read` scopes.
- Configure the client to receive the `driver-wallet-api` audience and role claims required by the API.
- API access is still authorized by server-side Keycloak token introspection. The UI's role display is only presentation; server checks are authoritative.
- Browser token is held in tab-scoped sessionStorage (not localStorage); avoid shared devices. For higher assurance, replace this lightweight SPA storage with a Backend-for-Frontend using Secure, HttpOnly, SameSite cookies.

## Admin role
Grant `sanad-admin` (realm role) or `admin` to authorized administrators. Ensure role claims are included in introspection responses. Never grant this role to ordinary driver accounts.

## Encrypted datasets
- CSV and JSON only; UTF-8; maximum 5 MiB and 10,000 records.
- Uploaded records are normalized to JSON and encrypted with Fernet authenticated encryption before storage.
- Configure `SANAD_DATA_ENCRYPTION_KEY` as a separately managed secret. Generate one with:
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Keep the key outside GitHub and rotate it through a controlled migration; losing it makes stored data unreadable.
- Configure `SANAD_DATA_DIR` to a durable mounted volume (for Render, attach a persistent disk and use its mount path). Without a persistent disk, local SQLite data may be lost on redeploy/restart.
- Seed and uploaded datasets are synthetic. No real driver or financial data should be uploaded.

## Deployment configuration
Set `PUBLIC_OIDC_CLIENT_ID`, `OIDC_REDIRECT_URI`, `SANAD_DATA_DIR`, and `SANAD_DATA_ENCRYPTION_KEY` in the hosting environment. Existing confidential API client settings remain separate:
`OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `KEYCLOAK_ISSUER`, `EXPECTED_AUDIENCE`, and `REQUIRED_WALLET_SCOPE`.

## Verification limits
Unit tests and a successful container build do not prove live Keycloak PKCE configuration, role claim mapping, durable disk attachment, key rotation, or production security. Keep Production Gate CLOSED until these are independently tested.
