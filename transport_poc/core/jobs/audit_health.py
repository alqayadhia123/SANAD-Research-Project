"""Authenticator posture report; does not invent data absent an identity source."""
from __future__ import annotations
import json, logging, os
from datetime import datetime, timezone
from pathlib import Path
from transport_poc.core.celery_app import celery_app
logger = logging.getLogger(__name__)

@celery_app.task(name="sanad.jobs.audit_health")
def run() -> dict:
    report_dir = Path(os.environ.get("SANAD_REPORT_DIR", "/tmp/sanad-reports"))
    report_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    report = {
        "generated_at": now.isoformat(),
        "status": "data_source_not_configured",
        "source": "Keycloak Admin API integration is not configured",
        "single_authenticator_users": None,
        "stale_authenticators": None,
        "no_authenticator_users": None,
    }
    path = report_dir / f"auth-health-{now:%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.warning("Authenticator posture report generated without identity data")
    return {"report_path": str(path), "status": report["status"]}
