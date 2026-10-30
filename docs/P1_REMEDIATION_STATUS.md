# SANAD P1 Remediation Status

**Status:** In progress — not accepted for operational or production use.

## Baseline
This work is based on hardening/transport-poc-2026-10-30, not main. SANAD
remains a Flask/Keycloak research PoC. No production deployment, real financial
wallet, WebAuthn ceremony, or production-grade HA is claimed.

## Implemented in this slice
- Tenant membership is derived only from verified claims supplied by upstream
  authentication middleware.
- X-Tenant-ID and subdomains are selectors, never proof of authorization.
- Missing identity returns 401; unauthorized tenant selection returns 403.
- Flask teardown resets the ContextVar token to prevent cross-request leakage.
- Redis lease acquire/renew/release use atomic Lua scripts.
- Redis errors and lease loss fail closed.
- Leader election returns a monotonically increasing fencing token.

## Not implemented or not verified
- Flask authentication middleware is not yet wired to set g.authenticated_claims;
  tenant-protected routes must not be enabled until this integration is complete.
- PostgreSQL RLS and transaction-scoped tenant binding are not implemented.
- Fencing tokens are not enforced by a durable downstream resource.
- Celery Beat is not guarded by this election primitive; do not run multiple Beat
  instances based on this module alone.
- Supervisor restart/backoff and shutdown behavior remain unimplemented.
- Cleanup, posture-audit, and suspicious-enrollment jobs remain unimplemented.
- No live Redis/PostgreSQL/Keycloak integration or container tests have run here.

## Acceptance gates
1. Wire verified OIDC claims into Flask request context.
2. Test PostgreSQL RLS with a non-owner app role: SELECT/INSERT/UPDATE isolation
   and connection-pool reuse.
3. Test Redis concurrency, renewal, expiry, ownership-safe release, outages,
   and stale-leader fencing.
4. Guard exactly one Beat scheduler and prove failover.
5. Test supervisor SIGTERM, child exit, bounded restart backoff, and deadlines.
6. Add idempotency and tenant partitioning tests for each background job.
7. Run CI, container smoke tests, and the full P0 regression suite.

**PRODUCTION_GATE=CLOSED**
