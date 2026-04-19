"""
High-performance asynchronous cache layer using Redis.
Implements Rank-1 patterns: connection pooling, atomic rate limiting, and memory fallbacks.
"""
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, cast
import redis.asyncio as redis
from .config import settings

logger = logging.getLogger(__name__)

class AsyncCache:
    """Resilient Redis cache with local memory failover capability."""

    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
        self.client: Optional[redis.Redis] = None
        self._memory_buckets: Dict[str, List[float]] = {}
        self._connection_warned = False

    async def connect(self) -> None:
        """Initializes the Redis connection pool with strict timeout protection."""
        if self.client:
            return

        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_TIMEOUT_SECONDS,
                max_connections=20,
                retry_on_timeout=True
            )
            await self.client.ping()
            if not self._connection_warned:
                logger.info("Redis infrastructure synchronized (Connection Pooling active).")
                self._connection_warned = True
        except Exception as e:
            if not self._connection_warned:
                logger.warning(f"Redis link failed: {e}. Engaging high-fidelity memory fallback.")
                self._connection_warned = True
            self.client = None

    async def close(self) -> None:
        """Gracefully terminates the Redis connection pool."""
        if self.client:
            try:
                await self.client.aclose()
                logger.info("Redis connection pool released.")
            except Exception as e:
                logger.debug(f"Shadow error during Redis shutdown: {e}")
            finally:
                self.client = None

    async def get(self, key: str) -> Optional[Any]:
        """Retrieves and deserializes a cached object."""
        if not self.client:
            return None
        try:
            val = await self.client.get(key)
            return json.loads(val) if val else None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.debug(f"Cache retrieval failure for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        """Serializes and stores an object with an optional TTL."""
        if not self.client:
            return
        try:
            await self.client.set(key, json.dumps(value), ex=ex)
        except redis.RedisError as e:
            logger.debug(f"Cache storage failure for {key}: {e}")

    async def is_rate_limited(self, key: str, capacity: int = 10, window: int = 60) -> bool:
        """
        Atomic sliding window rate limiter.
        Prioritizes Redis Lua execution; falls back to local memory on connection failure.
        """
        now = time.time()
        
        # 1. Distributed Logic (Redis Lua)
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
                # Use list-based arguments for keys and args to satisfy strict stubs
                result = await cast(Any, self.client.eval(lua, 1, [key], [str(now), str(capacity), str(window)]))
                return result == 1
            except redis.RedisError as e:
                logger.debug(f"Redis-side rate limit failure: {e}. Sinking to memory.")

        # 2. Local Fallback (Sliding Window)
        bucket = self._memory_buckets.setdefault(key, [])
        # Prune expired entries
        self._memory_buckets[key] = [t for t in bucket if t > now - window]
        
        if len(self._memory_buckets[key]) < capacity:
            self._memory_buckets[key].append(now)
            return False
        return True

cache = AsyncCache()


cache = AsyncCache()