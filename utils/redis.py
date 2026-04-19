import time
import json
import redis.asyncio as redis
import os
from typing import Any, Optional, Dict
from .config import settings
import logging

logger = logging.getLogger(__name__)

class AsyncCache:
    """
    High-performance asynchronous cache layer using Redis.
    Implements Rank-1 patterns including connection pooling, 
    atomic sliding-window rate limiting, and local memory fallbacks.
    """
    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
        self.client: Optional[redis.Redis] = None
        self._in_memory_limiters: Dict[str, list] = {}
        self._log_once_flag = False

    async def connect(self) -> None:
        """
        Establishes a resilient connection to the Redis infrastructure.
        Configures connection pooling for high-concurrency event traffic.
        """
        try:
            # Rank-1 Pattern: Connection pooling and timeout protection
            self.client = redis.from_url(
                self.redis_url, 
                decode_responses=True, 
                socket_connect_timeout=settings.REDIS_TIMEOUT_SECONDS,
                max_connections=20, # Pooling for high-load event scenarios
                retry_on_timeout=True
            )
            await self.client.ping()
            if not self._log_once_flag:
                logger.info("Connected to Redis infrastructure with connection pooling.")
                self._log_once_flag = True
        except Exception as e:
            if not self._log_once_flag:
                logger.warning(f"Redis unavailable: {e}. Activating high-resilience memory fallbacks.")
                self._log_once_flag = True
            self.client = None

    async def close(self) -> None:
        """Gracefully closes the Redis connection pool."""
        if self.client:
            try:
                await self.client.aclose()
                logger.info("Redis connection pool closed.")
            except Exception:
                pass

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a JSON-deserialized value from the cache.

        Args:
            key (str): The cache retrieval key.

        Returns:
            Optional[Any]: The deserialized value or None if missing/failed.
        """
        if not self.client:
            return None
        try:
            val = await self.client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.debug(f"Cache Get Error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        """
        Serializes and stores a value in the cache with an optional TTL.

        Args:
            key (str): The storage key.
            value (Any): Any JSON-serializable object.
            ex (Optional[int]): Time-to-live in seconds.
        """
        if not self.client:
            return
        try:
            await self.client.set(key, json.dumps(value), ex=ex)
        except Exception as e:
            logger.debug(f"Cache Set Error for {key}: {e}")

    async def is_rate_limited(self, key: str, capacity: int = 10, window: int = 60) -> bool:
        """
        Atomic Sliding Window rate limiter.
        Uses Lua scripts for Redis-side atomicity with a local in-memory fallback.

        Args:
            key (str): Unique identifier for the rate limit bucket (e.g., user IP).
            capacity (int): Maximum requests allowed in the window.
            window (int): Sliding window duration in seconds.

        Returns:
            bool: True if the request should be limited, False otherwise.
        """
        now = time.time()
        
        # 1. Atomic Redis Implementation (Lua)
        if self.client:
            lua_script = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local capacity = tonumber(ARGV[2])
            local window = tonumber(ARGV[3])
            
            redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
            local count = redis.call('ZCARD', key)
            
            if count < capacity then
                redis.call('ZADD', key, now, now)
                redis.call('EXPIRE', key, window)
                return 0 -- Not limited
            else
                return 1 -- Limited
            end
            """
            try:
                result = await self.client.eval(lua_script, 1, key, int(now), capacity, window)
                return result == 1
            except Exception as e:
                logger.debug(f"Lua Speed Limit Error: {e}. Falling back to memory.")

        # 2. Resilient In-Memory Fallback
        if key not in self._in_memory_limiters:
            self._in_memory_limiters[key] = []
        
        # Prune expired timestamps
        self._in_memory_limiters[key] = [t for t in self._in_memory_limiters[key] if t > now - window]
        
        if len(self._in_memory_limiters[key]) < capacity:
            self._in_memory_limiters[key].append(now)
            return False
        return True

cache = AsyncCache()