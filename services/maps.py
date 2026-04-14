import aiohttp
import asyncio
import googlemaps
import logging
from typing import Dict
from utils.config import settings
from utils.redis import cache

logger = logging.getLogger(__name__)

class MapsService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    async def get_walking_time(self, origins: list[Dict[str, float]], destinations: list[Dict[str, float]]) -> Dict[str, int]:
        """
        Returns a dictionary mapping 'lat,lng|lat,lng' origin-destination string pairs to transition time in seconds.
        Utilizes caching and exponential backoff retry logic.
        """
        origins_str = "|".join([f"{loc['latitude']},{loc['longitude']}" for loc in origins])
        dest_str = "|".join([f"{loc['latitude']},{loc['longitude']}" for loc in destinations])
        
        cache_key = f"maps:walking:batch:{hash(origins_str)}:{hash(dest_str)}"
        cached_val = await cache.get(cache_key)
        if cached_val is not None:
            return cached_val

        params = {
            "origins": origins_str,
            "destinations": dest_str,
            "mode": "walking",
            "key": self.api_key
        }

        max_retries = 3
        base_delay = 1
        result_matrix = {}

        async with aiohttp.ClientSession() as session:
            for attempt in range(max_retries):
                try:
                    async with session.get(self.base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("status") == "OK":
                                rows = data.get("rows", [])
                                for i, row in enumerate(rows):
                                    orig = origins[i]
                                    orig_key = f"{orig['latitude']},{orig['longitude']}"
                                    for j, element in enumerate(row.get("elements", [])):
                                        dest = destinations[j]
                                        dest_key = f"{dest['latitude']},{dest['longitude']}"
                                        if element.get("status") == "OK":
                                            duration = element["duration"]["value"]
                                            result_matrix[f"{orig_key}|{dest_key}"] = duration
                                
                                await cache.set(cache_key, result_matrix, ex=600)  # TTL 10 mins
                                return result_matrix
                        logger.warning(f"Maps API response not OK: {await response.text()}")
                except Exception as e:
                    logger.error(f"Maps API request failed on attempt {attempt+1}: {e}")
                
                await asyncio.sleep(base_delay * (2 ** attempt))
                
        # If it fails after retries
        logger.error("Failed to fetch walking time matrix after retries.")
        raise RuntimeError("Google Maps API failed to return walking time matrix")

maps_service = MapsService()
