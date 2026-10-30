"""Conservative session hygiene task.

Redis TTL is authoritative for expiry. This task reports keys lacking TTL; it
does not revoke sessions or call Keycloak admin APIs without a configured,
least-privilege integration.
"""
from __future__ import annotations
import logging, os
from transport_poc.core.celery_app import celery_app
logger = logging.getLogger(__name__)

@celery_app.task(name="sanad.jobs.cleanup_sessions")
def run() -> dict:
    import redis
    client = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379/0"))
    checked = 0
    missing_ttl = 0
    for key in client.scan_iter(match="sanad:session:*", count=200):
        checked += 1
        if client.ttl(key) == -1:
            missing_ttl += 1
    result = {"checked": checked, "sessions_missing_expiry": missing_ttl,
              "deleted": 0, "keycloak_revocations": 0,
              "note": "No session was deleted; expiry/revocation policy requires explicit integration."}
    logger.info("Session hygiene: %s", result)
    return result
