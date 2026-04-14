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

    async def is_rate_limited(self, key: str, capacity: int, refill_rate: float) -> bool:
        """Token bucket rate limiter using Lua script"""
        if not self.redis_client:
            return False # Fail open
        script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local requested = 1
        
        local bucket = redis.call("HMGET", key, "tokens", "last_refill")
        local tokens = tonumber(bucket[1])
        local last_refill = tonumber(bucket[2])
        
        if not tokens then
            tokens = capacity
            last_refill = now
        else
            local time_passed = now - last_refill
            local new_tokens = time_passed * refill_rate
            tokens = math.min(capacity, tokens + new_tokens)
            last_refill = now
        end
        
        if tokens >= requested then
            tokens = tokens - requested
            redis.call("HMSET", key, "tokens", tokens, "last_refill", last_refill)
            redis.call("EXPIRE", key, math.ceil(capacity / refill_rate))
            return 0
        else
            redis.call("HMSET", key, "tokens", tokens, "last_refill", last_refill)
            redis.call("EXPIRE", key, math.ceil(capacity / refill_rate))
            return 1
        end
        """
        import time
        try:
            result = await self.redis_client.eval(script, 1, key, capacity, refill_rate, time.time())
            return bool(result)
        except Exception as e:
            logger.warning(f"Rate limiter error: {e}")
            return False

cache = RedisCache()
