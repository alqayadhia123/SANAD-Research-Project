# Changelog

## Unreleased — P1 remediation

### Added
- Verified-Keycloak-claim-based tenant membership enforcement in Flask API.
- Redis Lua-based lease election with ownership-safe renewal/release and fencing token.
- Leader-elected periodic task dispatcher; no multi-instance Celery Beat is used.
- Celery worker, Redis service, and isolated Compose services.
- Conservative background jobs with explicit reporting when source integrations are absent.
- PostgreSQL RLS prerequisite migration that aborts if expected tables/columns are absent.
- Redis-backed integration tests in CI.

### Security and operational limitations
- Keycloak must emit a verified tenant_id or tenants claim through an approved protocol mapper.
- PostgreSQL persistence is not connected to the current synthetic wallet API; do not apply RLS migration before schema/role provisioning.
- Fencing tokens are not yet enforced by a durable downstream resource.
- Session cleanup, authenticator posture collection, and audit ingestion require real source integrations.
- Production gate remains closed pending live integration and deployment evidence.
