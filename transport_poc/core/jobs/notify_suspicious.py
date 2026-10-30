"""Detect repeated enrollment attempts and emit deduplicated webhook alerts."""
from __future__ import annotations
import json, logging, os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests
import redis
from transport_poc.core.celery_app import celery_app
logger = logging.getLogger(__name__)

@celery_app.task(name="sanad.jobs.notify_suspicious")
def run() -> dict:
    audit_dir = Path(os.environ.get("SANAD_AUDIT_DIR", "/var/log/sanad/audit"))
    now = datetime.now(timezone.utc)
    audit_file = audit_dir / f"{now:%Y-%m-%d}.jsonl"
    if not audit_file.is_file():
        return {"alerts": 0, "status": "audit_source_unavailable"}
    counts: Counter[tuple[str, str]] = Counter()
    with audit_file.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
                event = record.get("event", {})
                if event.get("event_type") != "enrollment_attempt":
                    continue
                timestamp = datetime.fromisoformat(str(event["timestamp"]).replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    continue
                if now - timedelta(minutes=5) <= timestamp <= now:
                    actor = str(event.get("actor_id", "unknown"))
                    tenant = str(event.get("tenant_id", "unknown"))
                    counts[(tenant, actor)] += 1
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                continue
    client = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379/0"))
    webhook = os.environ.get("SANAD_ALERT_WEBHOOK")
    sent = 0
    for (tenant, actor), count in counts.items():
        if count < 3:
            continue
        dedupe = f"sanad:alert:enrollment:{tenant}:{actor}:{now:%Y%m%d%H%M}"
        if not client.set(dedupe, "1", nx=True, ex=600):
            continue
        payload = {"severity": "warning", "event": "repeated_enrollment_attempts",
                   "tenant_id": tenant, "actor_id": actor, "count": count,
                   "window_minutes": 5, "timestamp": now.isoformat()}
        if webhook:
            try:
                response = requests.post(webhook, json=payload, timeout=3)
                response.raise_for_status()
                sent += 1
            except requests.RequestException:
                client.delete(dedupe)
                logger.exception("Alert webhook delivery failed")
        else:
            logger.warning("Suspicious enrollment detected; webhook not configured: %s", payload)
    return {"alerts_sent": sent, "actors_flagged": sum(1 for n in counts.values() if n >= 3)}
