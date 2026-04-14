import redis
import os
from .config import settings

def get_redis_client():
    try:
        # Pull the URL from environment variables
        redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
        
        # Initialize client with a timeout so it doesn't hang the app
        client = redis.from_url(
            redis_url, 
            decode_responses=True, 
            socket_connect_timeout=2
        )
        return client
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return None

redis_client = get_redis_client()