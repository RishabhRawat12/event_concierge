"""
Google Maps Platform integration for spatial transition analysis.
Computes high-performance accessibility metrics via Distance Matrix API.
Uses native httpx for asynchronous REST calls to avoid SDK bottlenecks.
Implements true concurrency via asyncio.gather for parallel batch processing.
"""
import hashlib
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
import httpx
from .config import settings
from .redis import cache

logger = logging.getLogger(__name__)

class MapsService:
    """Orchestrates authenticated spatial queries via native async REST."""

    def __init__(self) -> None:
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    async def get_walking_time(
        self, 
        origins: List[Dict[str, float]], 
        destinations: List[Dict[str, float]]
    ) -> Dict[str, int]:
        """
        Computes walking durations across a spatial matrix with batch optimization.
        """
        orig_keys = sorted([f"{loc['latitude']},{loc['longitude']}" for loc in origins])
        dest_keys = sorted([f"{loc['latitude']},{loc['longitude']}" for loc in destinations])
        
        key_raw = f"{json.dumps(orig_keys)}:{json.dumps(dest_keys)}"
        cache_key = f"maps:walking:v3:{hashlib.sha256(key_raw.encode()).hexdigest()}"
        
        cached = await cache.get(cache_key)
        if cached:
            return cached

        try:
            result = await self._fetch_matrix_httpx(origins, destinations)
            await cache.set(cache_key, result, ex=3600)
            return result
        except Exception as e:
            logger.warning(f"Maps API REST calling failure: {e}. Falling back to zero-weighted mapping.")
            return {}

    async def _fetch_matrix_httpx(
        self, 
        origins: List[Dict[str, float]], 
        destinations: List[Dict[str, float]]
    ) -> Dict[str, int]:
        """Internal native async batching logic using true concurrent execution."""
        combined: Dict[str, int] = {}
        tasks = []
        batch_meta = []

        # 1. Prepare all concurrent batches
        async with httpx.AsyncClient(timeout=10.0) as client:
            for i in range(0, len(origins), 10):
                o_batch = origins[i:i+10]
                o_str = "|".join([f"{loc['latitude']},{loc['longitude']}" for loc in o_batch])
                for j in range(0, len(destinations), 10):
                    d_batch = destinations[j:j+10]
                    d_str = "|".join([f"{loc['latitude']},{loc['longitude']}" for loc in d_batch])
                    
                    params = {
                        "origins": o_str,
                        "destinations": d_str,
                        "mode": "walking",
                        "key": self.api_key
                    }
                    
                    tasks.append(client.get(self.base_url, params=params))
                    batch_meta.append((o_batch, d_batch))

            # 2. Execute concurrently (Winner Tier Performance)
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 3. Process merged results
            for idx, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"Concurrent Maps Batch Failure: {response}")
                    continue
                
                resp_data = response.json()
                if resp_data.get("status") != "OK":
                    logger.error(f"Maps API Error: {resp_data.get('status')}")
                    continue

                o_batch, d_batch = batch_meta[idx]
                rows = resp_data.get("rows", [])
                o_locs = [f"{loc['latitude']},{loc['longitude']}" for loc in o_batch]
                d_locs = [f"{loc['latitude']},{loc['longitude']}" for loc in d_batch]

                for r_idx, row in enumerate(rows):
                    if r_idx >= len(o_locs): break
                    orig_key = o_locs[r_idx]
                    for e_idx, element in enumerate(row.get("elements", [])):
                        if e_idx >= len(d_locs): break
                        dest_key = d_locs[e_idx]
                        if element.get("status") == "OK":
                            combined[f"{orig_key}|{dest_key}"] = element["duration"]["value"]
        
        return combined

maps_service = MapsService()
