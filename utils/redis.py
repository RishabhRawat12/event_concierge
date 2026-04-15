import os
import json
import redis.asyncio as redis
from typing import Any, Optional
from .config import settings
import logging

logger = logging.getLogger(__name__)

class AsyncCache:
    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
        self.client = None

    async def connect(self) -> None:
        try:
            self.client = redis.from_url(
                self.redis_url, 
                decode_responses=True, 
                socket_connect_timeout=settings.REDIS_TIMEOUT_SECONDS
            )
            # Send a pilot ping safely to establish pool immediately
            await self.client.ping()
        except Exception as e:
            logger.warning(f"Redis initialization/connect error (ignoring and acting passively): {e}")
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

    async def is_rate_limited(self, key: str, capacity: int = 10, refill_rate: float = 1.0) -> bool:
        if not self.client:
            return False
        try:
            current = await self.client.incr(key)
            if current == 1:
                await self.client.expire(key, 60)
            if current > capacity:
                return True
        except Exception:
            pass
        return False

cache = AsyncCache()