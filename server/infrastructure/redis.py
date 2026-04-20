import json
import logging
import os
import time
import hashlib
import asyncio
import weakref
from typing import Any, Dict, List, Optional, cast, Callable, Awaitable
import redis.asyncio as redis
from .config import settings

logger = logging.getLogger(__name__)

class AsyncCache:
    """Resilient Redis cache & Pub/Sub for high-performance orchestration."""

    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
        self.client: Optional[redis.Redis] = None
        self._memory_buckets: Dict[str, List[float]] = {}
        self._connection_warned = False
        self._locks: weakref.WeakValueDictionary[str, asyncio.Lock] = weakref.WeakValueDictionary()

    async def connect(self) -> None:
        """Initializes the Redis connection pool."""
        if self.client:
            return

        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_TIMEOUT_SECONDS,
                max_connections=50,
                retry_on_timeout=True
            )
            await self.client.ping()
            if not self._connection_warned:
                logger.info("Redis infrastructure synchronized (Pub/Sub active).")
                self._connection_warned = True
        except Exception as e:
            if not self._connection_warned:
                logger.warning(f"Redis link failed: {e}. Engaging memory fallback.")
                self._connection_warned = True
            self.client = None

    async def clear(self) -> None:
        """Resets both Redis and memory-based state (Winner Tier Testing)."""
        if self.client:
            try:
                await self.client.flushdb()
            except Exception:
                pass
        self._memory_buckets = {}
        logger.debug("Cache state synchronized (Reset complete).")

    async def close(self) -> None:
        """Gracefully terminates the Redis connection pool."""
        if self.client:
            try:
                await self.client.aclose()
            except Exception:
                pass
            finally:
                self.client = None

    async def publish(self, channel: str, message: Any) -> int:
        """Publishes a tactical payload to a Redis channel for real-time distribution."""
        if not self.client:
            return 0
        try:
            payload = json.dumps(message)
            return await self.client.publish(channel, payload)
        except Exception as e:
            logger.debug(f"PubSub broadcasting failure: {e}")
            return 0

    async def subscribe(self, channel: str):
        """Returns a PubSub object subscribed to the specified channel."""
        if not self.client:
            return None
        ps = self.client.pubsub()
        await ps.subscribe(channel)
        return ps

    async def get_or_compute(
        self, 
        key: str, 
        compute_func: Callable[..., Awaitable[Any]], 
        ttl: int = 300,
        *args: Any, 
        **kwargs: Any
    ) -> Any:
        """Implements the 'Single-Flight' pattern."""
        cached = await self.get(key)
        if cached is not None:
            return cached

        lock = self._locks.get(key)
        if not lock:
            lock = asyncio.Lock()
            self._locks[key] = lock

        async with lock:
            cached = await self.get(key)
            if cached is not None:
                return cached
            
            result = await compute_func(*args, **kwargs)
            if result is not None:
                await self.set(key, result, ex=ttl)
            return result

    async def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        try:
            val = await self.client.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        if not self.client:
            return
        try:
            await self.client.set(key, json.dumps(value), ex=ex)
        except Exception:
            pass

    async def is_rate_limited(self, key: str, capacity: int = 10, window: int = 60) -> bool:
        """Atomic sliding window rate limiter."""
        now = time.time()
        if self.client:
            lua = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local capacity = tonumber(ARGV[2])
            local window = tonumber(ARGV[3])
            
            redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
            if redis.call('ZCARD', key) < capacity then
                redis.call('ZADD', key, now, now)
                redis.call('EXPIRE', key, window)
                return 0
            end
            return 1
            """
            try:
                result = await cast(Any, self.client.eval(lua, 1, [key], [str(now), str(capacity), str(window)]))
                return result == 1
            except Exception:
                pass

        bucket = self._memory_buckets.setdefault(key, [])
        self._memory_buckets[key] = [t for t in bucket if t > now - window]
        if len(self._memory_buckets[key]) < capacity:
            self._memory_buckets[key].append(now)
            return False
        return True

cache = AsyncCache()