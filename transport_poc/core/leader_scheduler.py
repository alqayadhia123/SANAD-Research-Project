"""Single-leader periodic dispatcher; intentionally replaces multi-instance Celery Beat."""
from __future__ import annotations
import logging, os, signal, time
import redis
from transport_poc.core.celery_app import celery_app
from transport_poc.core.scheduler import LeaderElection

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("sanad.leader_scheduler")
SCHEDULE = {
    "sanad.jobs.cleanup_sessions": int(os.getenv("SANAD_CLEANUP_INTERVAL", "3600")),
    "sanad.jobs.audit_health": int(os.getenv("SANAD_HEALTH_INTERVAL", "300")),
    "sanad.jobs.notify_suspicious": int(os.getenv("SANAD_ALERT_INTERVAL", "60")),
}

def main() -> int:
    stopping = False
    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    client = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379/0"))
    election = LeaderElection(client, ttl_seconds=30, renew_interval_seconds=8)
    last_dispatch: dict[str, float] = {}
    try:
        while not stopping:
            if not election.is_leader:
                try:
                    election.acquire()
                except redis.RedisError:
                    log.exception("Redis unavailable; scheduler remains inactive")
                if not election.is_leader:
                    time.sleep(3)
                    continue
            try:
                election.assert_leader()
                now = time.monotonic()
                for task_name, interval in SCHEDULE.items():
                    if interval < 1:
                        raise ValueError(f"Invalid interval for {task_name}")
                    if now - last_dispatch.get(task_name, 0) >= interval:
                        election.assert_leader()
                        celery_app.send_task(task_name, queue="sanad-background")
                        last_dispatch[task_name] = now
            except (redis.RedisError, RuntimeError):
                log.exception("Leader lease lost or unverifiable; dispatch halted")
                election.release()
            time.sleep(1)
    finally:
        election.release()
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
