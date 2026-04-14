import json
import logging
import redis.asyncio as redis
from redis.exceptions import RedisError, TimeoutError
from .config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                socket_timeout=settings.REDIS_TIMEOUT_SECONDS,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis gracefully.")
        except (RedisError, TimeoutError, OSError) as e:
            logger.warning(f"Failed to connect to Redis. Running without cache. Error: {e}")
            self.redis_client = None

    async def get(self, key: str):
        if not self.redis_client:
            return None
        try:
            val = await self.redis_client.get(key)
            return json.loads(val) if val else None
        except (RedisError, TimeoutError) as e:
            logger.warning(f"Redis get failed for {key}: {e}")
            return None

    async def set(self, key: str, value: dict, ex: int = 600):
        if not self.redis_client:
            return
        try:
            await self.redis_client.set(key, json.dumps(value), ex=ex)
        except (RedisError, TimeoutError) as e:
            logger.warning(f"Redis set failed for {key}: {e}")

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()

cache = RedisCache()
