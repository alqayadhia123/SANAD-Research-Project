"""Celery registration and job-safety contract tests."""
def test_background_jobs_are_registered():
    from transport_poc.core.celery_app import celery_app
    import transport_poc.core.jobs.cleanup_sessions
    import transport_poc.core.jobs.audit_health
    import transport_poc.core.jobs.notify_suspicious
    registered = set(celery_app.tasks)
    assert "sanad.jobs.cleanup_sessions" in registered
    assert "sanad.jobs.audit_health" in registered
    assert "sanad.jobs.notify_suspicious" in registered

def test_periodic_dispatch_has_single_leader_entrypoint():
    from transport_poc.core.leader_scheduler import SCHEDULE
    assert set(SCHEDULE) == {
        "sanad.jobs.cleanup_sessions",
        "sanad.jobs.audit_health",
        "sanad.jobs.notify_suspicious",
    }
    assert all(interval > 0 for interval in SCHEDULE.values())
