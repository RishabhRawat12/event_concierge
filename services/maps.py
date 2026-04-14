import aiohttp
import asyncio
import googlemaps
import logging
from typing import Dict, List, Optional, Union
from utils.config import settings
from utils.redis import cache

logger = logging.getLogger(__name__)

class MapsService:
    def __init__(self) -> None:
        """
        Initializes the Maps Service orchestrating authenticated calls via the official SDK structure.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError: Automatically thrown internally if keys are missing from context.
        """
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.gmaps_client = googlemaps.Client(key=self.api_key)

    async def get_walking_time(self, origins: List[Dict[str, float]], destinations: List[Dict[str, float]]) -> Dict[str, int]:
        """
        Returns a dictionary mapping 'lat,lng|lat,lng' origin-destination string pairs to transition time in seconds.
        Utilizes caching and exponential backoff retry logic alongside the official maps Python package.

        Args:
            origins (List[Dict[str, float]]): The starting spatial coordinates for the matrix dimension.
            destinations (List[Dict[str, float]]): The target spatial coordinates for the matrix dimension.

        Returns:
            Dict[str, int]: A flattened dictionary defining explicit walking delays.

        Raises:
            RuntimeError: If the Google Maps API inherently fails to return the required transition dictionary safely.
        """
        origins_list = [f"{loc['latitude']},{loc['longitude']}" for loc in origins]
        dest_list = [f"{loc['latitude']},{loc['longitude']}" for loc in destinations]
        
        cache_key = f"maps:walking:batch:{hash(str(origins_list))}:{hash(str(dest_list))}"
        cached_val = await cache.get(cache_key)
        if cached_val is not None:
            return cached_val

        max_retries = 3
        base_delay = 1.0
        result_matrix = {}

        def _fetch_matrix() -> Dict:
            return self.gmaps_client.distance_matrix(origins_list, dest_list, mode="walking")

        for attempt in range(max_retries):
            try:
                data = await asyncio.to_thread(_fetch_matrix)
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
                logger.warning(f"Maps API response not OK: {data}")
            except Exception as e:
                logger.error(f"Maps API request failed on attempt {attempt+1}: {e}")
            
            await asyncio.sleep(base_delay * (2 ** attempt))
                
        # If it fails after retries
        logger.error("Failed to fetch walking time matrix after retries.")
        raise RuntimeError("Google Maps API failed to return walking time matrix")

maps_service = MapsService()
