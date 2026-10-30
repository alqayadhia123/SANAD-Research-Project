# SANAD Keycloak — Render Free Lab

This directory contains the container definition for the SANAD identity service.

## Runtime configuration

Configure these values in the Render service dashboard (never commit credentials):

- `KC_DB=postgres`
- `KC_DB_URL=jdbc:postgresql://<INTERNAL_HOST>:5432/<DATABASE_NAME>`
- `KC_DB_USERNAME=<DATABASE_USER>`
- `KC_DB_PASSWORD=<DATABASE_PASSWORD>`
- `KC_BOOTSTRAP_ADMIN_USERNAME=<ADMIN_USERNAME>`
- `KC_BOOTSTRAP_ADMIN_PASSWORD=<LONG_RANDOM_SECRET>`
- `KC_HTTP_ENABLED=true`
- `KC_PROXY_HEADERS=xforwarded`
- `KC_HOSTNAME=https://<RENDER_SERVICE_HOSTNAME>`
- `KC_HEALTH_ENABLED=true`

Use the PostgreSQL **Internal Database URL** from the same Render region (Frankfurt).
Do not use the external URL for service-to-service traffic.

After the first successful deployment, create the realm `sanad-lab` in the Admin Console.
The admin bootstrap credentials must be unique and stored in a password manager.

## Security and scope

- This is a research/lab deployment, not production-ready identity infrastructure.
- Do not use `start-dev` on a public service.
- Restrict administrative access and rotate bootstrap credentials after initial setup.
- Render Free services may sleep, restart, or have limited resources; the free PostgreSQL instance has an expiry date.
- Do not store real driver identity documents, payment credentials, or production personal data in this lab.
