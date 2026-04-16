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
        import hashlib
        import json

        origins_list = sorted([f"{loc['latitude']},{loc['longitude']}" for loc in origins])
        dest_list = sorted([f"{loc['latitude']},{loc['longitude']}" for loc in destinations])
        
        # Security & Efficiency: Use deterministic SHA256 instead of native volatile hash()
        # Sorting ensures that the same set of locations always yields the same cache key regardless of order
        h_orig = hashlib.sha256(json.dumps(origins_list).encode()).hexdigest()
        h_dest = hashlib.sha256(json.dumps(dest_list).encode()).hexdigest()
        cache_key = f"maps:walking:batch:{h_orig}:{h_dest}"
        
        cached_val = await cache.get(cache_key)
        if cached_val is not None:
            return cached_val

        max_retries = 3
        base_delay = 1.0

        def _fetch_matrix_all() -> Dict[str, int]:
            combined_matrix = {}
            # API constraint: origins x destinations <= 100 elements. 10x10 chunking.
            for i in range(0, len(origins_list), 10):
                o_chunk = origins_list[i:i+10]
                o_raw = origins[i:i+10]
                for j in range(0, len(dest_list), 10):
                    d_chunk = dest_list[j:j+10]
                    d_raw = destinations[j:j+10]
                    
                    data = self.gmaps_client.distance_matrix(o_chunk, d_chunk, mode="walking")
                    if data.get("status") == "OK":
                        rows = data.get("rows", [])
                        for r_idx, row in enumerate(rows):
                            orig = o_raw[r_idx]
                            orig_key = f"{orig['latitude']},{orig['longitude']}"
                            for e_idx, element in enumerate(row.get("elements", [])):
                                dest = d_raw[e_idx]
                                dest_key = f"{dest['latitude']},{dest['longitude']}"
                                if element.get("status") == "OK":
                                    duration_val = element["duration"]["value"]
                                    combined_matrix[f"{orig_key}|{dest_key}"] = duration_val
                    else:
                        raise RuntimeError(f"Maps API response not OK: {data}")
            return combined_matrix

        for attempt in range(max_retries):
            try:
                result_matrix = await asyncio.to_thread(_fetch_matrix_all)
                await cache.set(cache_key, result_matrix, ex=600)  # TTL 10 mins
                return result_matrix
            except Exception as e:
                logger.error(f"Maps API request failed on attempt {attempt+1}: {e}")
            
            await asyncio.sleep(base_delay * (2 ** attempt))
                
        # If it fails after retries
        logger.error("Failed to fetch walking time matrix after retries.")
        raise RuntimeError("Google Maps API failed to return walking time matrix")

maps_service = MapsService()
