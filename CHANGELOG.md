# Changelog

All notable changes to SANAD are documented here. SANAD remains a research proof of concept.

## [Unreleased] — P1 operational remediation

### Added
- Keycloak-introspection-backed tenant membership enforcement.
- Atomic Redis lease election and a leader-elected Celery task dispatcher.
- Redis, API, worker, and scheduler Compose services.
- Conservative session-hygiene, authenticator-posture, and suspicious-enrollment tasks.
- Fail-closed PostgreSQL RLS prerequisite migration.
- Redis-backed leader-election integration tests and CI service.

### Security and operational limitations
- Tenant claims must be explicitly mapped by Keycloak.
- PostgreSQL persistence is not connected to the synthetic wallet API.
- Fencing tokens are not yet enforced at a durable write boundary.
- Session revocation, authenticator inventory, and audit ingestion need source integrations.
- Production gate remains closed pending live integration and deployment evidence.

## [0.1.0] — P0 security baseline

### Added
- Fail-closed Keycloak bearer-token introspection for protected endpoints.
- Security response headers and API no-store caching.
- Python project metadata, test setup, GitHub Actions CI, security and contributor documentation.
- Container and deployment configuration for the isolated research lab.

### Changed
- Removed authentication bypass behavior from protected API routes.
- Clarified that wallet and route values are synthetic and that WebAuthn enrollment is not implemented.

### Known limitations
- WebAuthn registration/authentication ceremony remains unimplemented (HTTP 501).
- Independent out-of-band approval and account recovery are not implemented.
- Keycloak development-mode configuration is for research only.
- No production certification or resistance claim is made.
