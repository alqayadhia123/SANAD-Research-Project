# Changelog

All notable changes to this research proof of concept are documented here.

## [Unreleased]

### Security and reliability
- Removed the environment-variable authentication bypass from the driver API. API access now always requires a Bearer token validated through Keycloak introspection.
- Kept identity-provider failures fail-closed; missing client credentials or an unavailable introspection endpoint do not grant access.
- Added automated tests for missing credentials, inactive tokens, and valid introspection responses.
- Aligned the API container's Gunicorn listener with the port exposed by the Compose lab.
- Added baseline contribution, security-reporting, and conduct policies.

### Limitations
- WebAuthn registration and authentication ceremonies are not implemented.
- Wallet and route responses contain synthetic demonstration data only; no real funds, payment processing, or financial ledger are connected.
- The Compose Keycloak service uses `start-dev` and is for an isolated local research lab only.
- No production readiness, penetration-test result, security certification, or end-to-end deployment validation is claimed.
