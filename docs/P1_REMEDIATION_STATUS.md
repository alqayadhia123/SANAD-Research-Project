# SANAD P1 Remediation Status

**Status: IN PROGRESS — not approved for production.**

## Implemented in this branch
- Flask API introspects bearer tokens at the before-request boundary; tenant-protected endpoints run only after successful Keycloak introspection.
- Tenant membership is derived only from claims returned by the trusted Keycloak introspection endpoint. Header/subdomain values are selectors, never authorization evidence.
- Missing identity returns 401; unauthorized tenant selection returns 403; ambiguous multi-tenant identity requires an explicit selector.
- Request teardown resets the ContextVar token.
- Redis leader lease acquire/renew/release use atomic Lua scripts, owner-checked release, lease-loss detection, and a monotonic fencing counter.
- A dedicated leader-elected dispatcher sends periodic Celery tasks. It halts dispatch if leadership cannot be verified.
- Redis, API, worker, and scheduler are separate Compose services.
- Redis lease integration tests are wired into CI.
- RLS prerequisite migration is fail-closed and transaction-local.

## Explicit limitations
- Keycloak realm/client configuration must expose tenant_id or tenants as introspection claims. The application intentionally denies tenant access if the claim is absent.
- PostgreSQL is not yet used by the wallet API. The migration requires pre-existing drivers, sessions, and audit_logs tables with tenant_id; it aborts otherwise. Apply only after provisioning a separate non-owner, non-superuser, non-BYPASSRLS runtime role.
- Application code does not yet open tenant-scoped DB transactions or prove pool-reset behavior.
- Fencing tokens are generated but no downstream database/resource rejects stale tokens yet.
- Session hygiene reports missing Redis TTLs; it does not delete sessions or revoke Keycloak sessions.
- Authenticator posture report explicitly reports unavailable data until Keycloak Admin API integration exists.
- Suspicious-enrollment detection requires an actual JSONL audit feed and webhook configuration; the API audit feed is not yet wired.
- The supervisor module is for local lab use; Compose uses one process per container and restart policies.
- No claim is made that Docker, Keycloak, PostgreSQL, or a production deployment was executed from this GitHub-only session.

## Required acceptance gates
1. Configure Keycloak protocol mapper and test real introspection responses for one-tenant, multi-tenant, and no-membership identities.
2. Provision tenant tables and a restricted DB runtime role; test RLS SELECT/INSERT/UPDATE and connection-pool reuse.
3. Enforce fencing token at the durable downstream write boundary.
4. Run two scheduler replicas against Redis; test failover, TTL expiry, Redis outage, and no duplicate dispatch.
5. Add durable audit feed integration and idempotent alert delivery tests.
6. Integrate Keycloak authenticator inventory and safe session revocation policy.
7. Run complete P0 regression, CI, Compose smoke, and failure-injection tests.

**PRODUCTION_GATE=CLOSED**
