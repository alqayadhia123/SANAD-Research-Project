"""Celery application for SANAD background processing."""
from __future__ import annotations
import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery(
    "sanad",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "transport_poc.core.jobs.cleanup_sessions",
        "transport_poc.core.jobs.audit_health",
        "transport_poc.core.jobs.notify_suspicious",
    ],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=240,
    task_time_limit=300,
    broker_connection_retry_on_startup=True,
    task_default_retry_delay=30,
    task_max_retries=3,
)
