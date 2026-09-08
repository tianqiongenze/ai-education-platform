"""Two-level cache: L1 = in-process (cachetools TTLCache), L2 = Redis.

Pattern: cache-aside.
  Read:  L1 -> (miss) -> L2 -> (miss) -> caller loads -> backfill L1 + L2.
  Write: invalidate both levels (delete key from L1 and L2).

L1 is per-process and bounded (size + TTL) for sub-millisecond local hits.
L2 (Redis) is shared across processes/replicas and survives restarts.
If Redis is unreachable, the cache degrades gracefully to L1-only + memory L2.
"""
from __future__ import annotations
import os
import time
import threading
from typing import Dict, Optional
from cachetools import TTLCache
from industrial.use_cases.ports import CachePort


class _MemoryCache(CachePort):
    """In-memory fallback (used as L2 when Redis is unavailable, e.g. in tests)."""
    def __init__(self):
        self._store: Dict[str, tuple[str, float]] = {}
        self._counters: Dict[str, int] = {}
    def get(self, key):
        item = self._store.get(key)
        if not item:
            return None
        val, exp = item
        if exp and time.time() > exp:
            self._store.pop(key, None)
            return None
        return val
    def set(self, key, value, ttl=60):
        self._store[key] = (value, time.time() + ttl if ttl else 0)
    def delete(self, key):
        self._store.pop(key, None)
    def incr(self, key):
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]


class RedisCache(CachePort):
    def __init__(self, url: str | None = None):
        import redis
        self._client = redis.Redis.from_url(
            url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    def get(self, key): return self._client.get(key)
    def set(self, key, value, ttl=60): self._client.set(key, value, ex=ttl)
    def delete(self, key): self._client.delete(key)
    def incr(self, key): return self._client.incr(key)
    def ping(self) -> bool:
        try:
            return bool(self._client.ping())
        except Exception:
            return False


class TwoLevelCache(CachePort):
    """L1 (cachetools, in-process) + L2 (Redis, shared). Cache-aside with invalidation."""

    def __init__(self, l2: CachePort, *, l1_maxsize: int = 4096, l1_ttl: int = 120):
        self._l1: TTLCache = TTLCache(maxsize=l1_maxsize, ttl=l1_ttl)
        self._l2 = l2
        self._lock = threading.Lock()
        # hit/miss counters for analysis
        self.l1_hits = 0
        self.l2_hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key) -> Optional[str]:
        with self._lock:
            v = self._l1.get(key)
            if v is not None:
                self.l1_hits += 1
                return v
        v = self._l2.get(key)
        if v is not None:
            self.l2_hits += 1
            decoded = v.decode() if isinstance(v, (bytes, bytearray)) else v
            with self._lock:
                self._l1[key] = decoded
            return decoded
        with self._lock:
            self.misses += 1
        return None

    def set(self, key, value, ttl=60):
        with self._lock:
            self._l1[key] = value
        self._l2.set(key, value, ttl=ttl)

    def delete(self, key):
        """Invalidate a key on write (write-through invalidation)."""
        with self._lock:
            self._l1.pop(key, None)
            self.evictions += 1
        self._l2.delete(key)

    def incr(self, key):
        # counters only live in L2 (must be consistent across instances)
        return self._l2.incr(key)

    def stats(self) -> dict:
        total = self.l1_hits + self.l2_hits + self.misses
        hit_rate = (self.l1_hits + self.l2_hits) / total * 100.0 if total else 0.0
        return {
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total,
        }


def make_cache() -> CachePort:
    """Factory: two-level cache (L1 cachetools + L2 Redis), with graceful fallback."""
    try:
        redis_cache = RedisCache()
        if redis_cache.ping():
            return TwoLevelCache(redis_cache)
    except Exception:
        pass
    # Redis unavailable -> L1 + memory L2 (still two levels, both in-process).
    return TwoLevelCache(_MemoryCache())
