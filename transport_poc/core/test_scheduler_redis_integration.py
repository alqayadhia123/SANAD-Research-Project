"""Real Redis integration tests; CI supplies REDIS_URL and a Redis service."""
import os
import uuid
import pytest
import redis
from transport_poc.core.scheduler import LeaderElection

@pytest.mark.integration
def test_redis_lease_is_exclusive_and_fencing_is_monotonic():
    url = os.getenv("REDIS_URL")
    if not url:
        pytest.skip("REDIS_URL not configured")
    client = redis.Redis.from_url(url)
    client.ping()
    key = "sanad:test:leader:" + uuid.uuid4().hex
    first = LeaderElection(client, lock_key=key, ttl_seconds=9, renew_interval_seconds=2)
    second = LeaderElection(client, lock_key=key, ttl_seconds=9, renew_interval_seconds=2)
    try:
        a = first.acquire()
        assert a is not None
        assert second.acquire() is None
        assert first.assert_leader() == a.fencing_token
    finally:
        first.release()
    b = second.acquire()
    try:
        assert b is not None
        assert b.fencing_token > a.fencing_token
    finally:
        second.release()
