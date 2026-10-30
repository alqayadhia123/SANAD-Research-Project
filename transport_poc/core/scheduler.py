"""Atomic Redis lease-based leader election primitives.
This elects a scheduler leader; it does not launch or guard Celery Beat.
Downstream writes must enforce the returned monotonically increasing fencing token.
"""
from __future__ import annotations
import logging, os, threading, uuid
from dataclasses import dataclass
import redis

logger = logging.getLogger(__name__)
_ACQUIRE = """
if redis.call('EXISTS', KEYS[1]) == 1 then return false end
local fence = redis.call('INCR', KEYS[2])
local value = ARGV[1] .. ':' .. fence
redis.call('PSETEX', KEYS[1], ARGV[2], value)
return {value, fence}
"""
_RENEW = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('PEXPIRE', KEYS[1], ARGV[2])
end
return 0
"""
_RELEASE = """
if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) end
return 0
"""

@dataclass(frozen=True)
class Leadership:
    owner_value: str
    fencing_token: int

class LeaderElection:
    def __init__(self, client: redis.Redis, *, lock_key: str = "sanad:{scheduler}:leader",
                 ttl_seconds: int = 60, renew_interval_seconds: int | None = None) -> None:
        if ttl_seconds < 6:
            raise ValueError("ttl_seconds must be at least 6")
        self.redis, self.lock_key = client, lock_key
        self.fence_key = lock_key.rsplit(":", 1)[0] + ":fence"
        self.ttl_ms = ttl_seconds * 1000
        self.renew_interval = renew_interval_seconds or max(1, ttl_seconds // 3)
        if self.renew_interval >= ttl_seconds:
            raise ValueError("renew interval must be shorter than lease TTL")
        self.instance_id = f"{os.getpid()}-{uuid.uuid4().hex}"
        self.leadership: Leadership | None = None
        self._stop, self._lost = threading.Event(), threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_leader(self) -> bool:
        return self.leadership is not None and not self._lost.is_set()

    def acquire(self) -> Leadership | None:
        result = self.redis.eval(_ACQUIRE, 2, self.lock_key, self.fence_key,
                                 self.instance_id, self.ttl_ms)
        if not result:
            return None
        raw = result[0]
        owner = raw.decode() if isinstance(raw, bytes) else str(raw)
        self.leadership = Leadership(owner, int(result[1]))
        self._lost.clear()
        self._stop.clear()
        self._thread = threading.Thread(target=self._renew_loop, name="sanad-leader-lease", daemon=True)
        self._thread.start()
        logger.info("Scheduler leadership acquired; fencing_token=%d", self.leadership.fencing_token)
        return self.leadership

    def _renew_loop(self) -> None:
        while not self._stop.wait(self.renew_interval):
            leadership = self.leadership
            if leadership is None:
                self._lost.set()
                return
            try:
                renewed = self.redis.eval(_RENEW, 1, self.lock_key, leadership.owner_value, self.ttl_ms)
                if int(renewed or 0) != 1:
                    logger.error("Scheduler lease ownership lost")
                    self._lost.set()
                    return
            except redis.RedisError:
                logger.exception("Redis unavailable during lease renewal")
                self._lost.set()
                return

    def assert_leader(self) -> int:
        leadership = self.leadership
        if leadership is None or self._lost.is_set():
            raise RuntimeError("Scheduler is not the current leader")
        try:
            current = self.redis.get(self.lock_key)
        except redis.RedisError as exc:
            self._lost.set()
            raise RuntimeError("Cannot verify scheduler leadership") from exc
        if current is None:
            self._lost.set()
            raise RuntimeError("Scheduler lease expired")
        value = current.decode() if isinstance(current, bytes) else str(current)
        if value != leadership.owner_value:
            self._lost.set()
            raise RuntimeError("Scheduler leadership was superseded")
        return leadership.fencing_token

    def release(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1, self.renew_interval + 1))
        leadership = self.leadership
        if leadership is not None:
            try:
                self.redis.eval(_RELEASE, 1, self.lock_key, leadership.owner_value)
            except redis.RedisError:
                logger.exception("Could not release scheduler lease; TTL will expire")
        self.leadership = None
        self._lost.set()
