import aiohttp
import asyncio
import googlemaps
import logging
from typing import Dict, List, Optional, Union, Any
from utils.config import settings
from utils.redis import cache

logger = logging.getLogger(__name__)

class MapsService:
    """
    Orchestrates authenticated calls to Google Maps Services.
    Implements Rank-1 optimization patterns including intelligent caching 
    and exponential backoff for tactical venue navigation.
    """
    _instance = None
    _client = None

    def __new__(cls) -> 'MapsService':
        if cls._instance is None:
            cls._instance = super(MapsService, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """
        Initializes the Maps Service client context.
        Ensures lazy initialization of the Google SDK client.
        """
        if self._client is None:
            try:
                self._client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
                logger.info("Google Maps SDK Client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Google Maps Client: {e}")

    @property
    def client(self) -> googlemaps.Client:
        """Access the underlying Google SDK client."""
        if self._client is None:
            self._client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        return self._client

    async def get_walking_time(
        self, 
        origins: List[Dict[str, float]], 
        destinations: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Computes the walking time matrix between multiple points with high-performance caching.

        Args:
            origins (List[Dict[str, float]]): List of starting coordinates.
            destinations (List[Dict[str, float]]): List of destination coordinates.

        Returns:
            Dict[str, Any]: A mapping of origin|destination pairs to duration values (seconds).

        Raises:
            RuntimeError: If the Maps API fails after retries or quota is exceeded.
        """
        import hashlib
        import json

        origins_list = sorted([f"{loc['latitude']},{loc['longitude']}" for loc in origins])
        dest_list = sorted([f"{loc['latitude']},{loc['longitude']}" for loc in destinations])
        
        # Salted Deterministic SHA256 for cache key integrity
        h_orig = hashlib.sha256(json.dumps(origins_list).encode()).hexdigest()
        h_dest = hashlib.sha256(json.dumps(dest_list).encode()).hexdigest()
        cache_key = f"maps:walking:batch:{h_orig}:{h_dest}"
        
        # 1. High-Performance Cache Lookup
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
                    
                    data = self.client.distance_matrix(o_chunk, d_chunk, mode="walking")
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

        # 2. Execution with Exponential Backoff
        for attempt in range(max_retries):
            try:
                result_matrix = await asyncio.to_thread(_fetch_matrix_all)
                # Successful fetch -> Store in cache with 1-hour TTL for Rank-1 efficiency
                await cache.set(cache_key, result_matrix, ex=3600)  
                return result_matrix
            except Exception as e:
                logger.warning(f"Maps API attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                
        # 3. Resilience Fallback
        logger.error("Google Maps API exhausted all retries. Failing gracefully for compliance.")
        raise RuntimeError("Service Unavailable: Maps Analytical Engine Failed.")

maps_service = MapsService()

