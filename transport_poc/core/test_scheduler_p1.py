"""Unit tests for atomic leader lease behavior."""
import pytest

from transport_poc.core.scheduler import LeaderElection, _ACQUIRE, _RENEW, _RELEASE


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.fences = {}

    def eval(self, script, numkeys, *args):
        if script == _ACQUIRE:
            lock_key, fence_key, instance_id, _ttl = args
            if lock_key in self.values:
                return None
            fence = self.fences.get(fence_key, 0) + 1
            self.fences[fence_key] = fence
            value = f"{instance_id}:{fence}"
            self.values[lock_key] = value
            return [value, fence]
        if script == _RENEW:
            lock_key, owner, _ttl = args
            return 1 if self.values.get(lock_key) == owner else 0
        if script == _RELEASE:
            lock_key, owner = args
            if self.values.get(lock_key) == owner:
                del self.values[lock_key]
                return 1
            return 0
        raise AssertionError("Unexpected Lua script")

    def get(self, key):
        return self.values.get(key)


def test_only_one_instance_acquires_lease():
    client = FakeRedis()
    first = LeaderElection(client, ttl_seconds=9, renew_interval_seconds=2)
    second = LeaderElection(client, ttl_seconds=9, renew_interval_seconds=2)
    leadership = first.acquire()
    try:
        assert leadership is not None
        assert leadership.fencing_token == 1
        assert second.acquire() is None
        assert first.assert_leader() == 1
    finally:
        first.release()
        second.release()


def test_fencing_token_increases_after_lease_release():
    client = FakeRedis()
    first = LeaderElection(client, ttl_seconds=9, renew_interval_seconds=2)
    second = LeaderElection(client, ttl_seconds=9, renew_interval_seconds=2)
    one = first.acquire()
    first.release()
    two = second.acquire()
    try:
        assert one is not None and two is not None
        assert two.fencing_token > one.fencing_token
    finally:
        second.release()


def test_stale_leader_cannot_delete_new_owners_lease():
    client = FakeRedis()
    first = LeaderElection(client, ttl_seconds=9, renew_interval_seconds=2)
    leadership = first.acquire()
    assert leadership is not None
    client.values[first.lock_key] = "replacement-owner:99"
    first.release()
    assert client.values[first.lock_key] == "replacement-owner:99"


def test_renew_interval_must_be_shorter_than_ttl():
    with pytest.raises(ValueError):
        LeaderElection(FakeRedis(), ttl_seconds=10, renew_interval_seconds=10)
