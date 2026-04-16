import time
import json
import redis.asyncio as redis
import os
from typing import Any, Optional
from .config import settings
import logging

logger = logging.getLogger(__name__)

class AsyncCache:
    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
        self.client = None
        self._in_memory_limiters: dict = {}
        self._log_once_flag = False

    async def connect(self) -> None:
        try:
            self.client = redis.from_url(
                self.redis_url, 
                decode_responses=True, 
                socket_connect_timeout=settings.REDIS_TIMEOUT_SECONDS
            )
            await self.client.ping()
            if not self._log_once_flag:
                logger.info("Connected to Redis infrastructure successfully.")
                self._log_once_flag = True
        except Exception as e:
            if not self._log_once_flag:
                logger.info(f"Redis unavailable: {e}. Switching to high-resilience in-memory fallbacks.")
                self._log_once_flag = True
            self.client = None

    async def close(self) -> None:
        if self.client:
            try:
                await self.client.aclose()
            except Exception:
                pass

    async def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        try:
            val = await self.client.get(key)
            if val:
                return json.loads(val)
            return None
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
        """
        Implements a Sliding Window rate limiter using Redis ZSETs (atomic Lua) 
        with a local in-memory fallback for high availability.
        """
        now = time.time()
        
        # Redis implementation
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
                return 0
            else
                return 1
            end
            """
            try:
                result = await self.client.eval(lua_script, 1, key, int(now), capacity, window)
                return result == 1
            except Exception as e:
                logger.debug(f"Redis Eval Error: {e}")
                # Fall through to in-memory on redis script error

        # In-memory Fallback (High Resilience)
        if key not in self._in_memory_limiters:
            self._in_memory_limiters[key] = []
        
        # Cleanup old entries
        self._in_memory_limiters[key] = [t for t in self._in_memory_limiters[key] if t > now - window]
        
        if len(self._in_memory_limiters[key]) < capacity:
            self._in_memory_limiters[key].append(now)
            return False
        return True

cache = AsyncCache()