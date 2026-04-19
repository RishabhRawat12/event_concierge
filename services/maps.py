"""
Google Maps Platform integration for spatial transition analysis.
Computes high-performance accessibility metrics via Distance Matrix API.
Implements exponential backoff and batched navigation for architectural efficiency.
"""
import asyncio
import hashlib
import json
import logging
from typing import Dict, List, Optional
import googlemaps # type: ignore
from utils.config import settings
from utils.redis import cache

logger = logging.getLogger(__name__)

class MapsService:
    """Orchestrates authenticated spatial queries via Google SDK."""

    _instance: Optional['MapsService'] = None
    _client: Optional[googlemaps.Client] = None

    def __new__(cls) -> 'MapsService':
        if cls._instance is None:
            cls._instance = super(MapsService, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Lazy initialization of the Maps client context."""
        if self._client is None:
            try:
                self._client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
            except Exception as e:
                logger.error(f"Maps SDK Link Failure: {e}")

    @property
    def client(self) -> googlemaps.Client:
        """Provides access to the shared Google Maps Client instance."""
        if self._client is None:
            self._client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        return self._client

    async def get_walking_time(
        self, 
        origins: List[Dict[str, float]], 
        destinations: List[Dict[str, float]]
    ) -> Dict[str, int]:
        """
        Computes walking durations across a spatial matrix with batch optimization.

        Args:
            origins: Starting coordinate pairs.
            destinations: Target coordinate pairs.

        Returns:
            Mapping of 'origin|destination' pairs to travel time in seconds.
        """
        orig_keys = sorted([f"{loc['latitude']},{loc['longitude']}" for loc in origins])
        dest_keys = sorted([f"{loc['latitude']},{loc['longitude']}" for loc in destinations])
        
        # Deterministic cache key based on coordinate signatures
        key_raw = f"{json.dumps(orig_keys)}:{json.dumps(dest_keys)}"
        cache_key = f"maps:walking:v1:{hashlib.sha256(key_raw.encode()).hexdigest()}"
        
        # Priority 1: High-Performance Cache lookup
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # Priority 2: Execution with Exponential Backoff
        for attempt in range(3):
            try:
                result = await asyncio.to_thread(self._fetch_matrix_batch, origins, destinations)
                await cache.set(cache_key, result, ex=3600)  # 1-hour tactical cache TTL
                return result
            except Exception as e:
                logger.warning(f"Maps API attempt {attempt+1} failed: {e}. Retrying.")
                if attempt < 2:
                    await asyncio.sleep(1.0 * (2 ** attempt))

        logger.error("Maps Engine Exhausted. Falling back to deterministic zero-weighted mapping.")
        return {}

    def _fetch_matrix_batch(
        self, 
        origins: List[Dict[str, float]], 
        destinations: List[Dict[str, float]]
    ) -> Dict[str, int]:
        """Internal synchronous batching logic for the Distance Matrix API."""
        combined: Dict[str, int] = {}
        # Google API Constraint: origins x destinations <= 100
        for i in range(0, len(origins), 10):
            o_batch = origins[i:i+10]
            o_locs = [f"{loc['latitude']},{loc['longitude']}" for loc in o_batch]
            for j in range(0, len(destinations), 10):
                d_batch = destinations[j:j+10]
                d_locs = [f"{loc['latitude']},{loc['longitude']}" for loc in d_batch]
                
                resp = self.client.distance_matrix(o_locs, d_locs, mode="walking")
                if resp.get("status") != "OK":
                    raise RuntimeError(f"Maps API error: {resp.get('status')}")
                
                rows = resp.get("rows", [])
                for r_idx, row in enumerate(rows):
                    orig_key = o_locs[r_idx]
                    for e_idx, element in enumerate(row.get("elements", [])):
                        dest_key = d_locs[e_idx]
                        if element.get("status") == "OK":
                            combined[f"{orig_key}|{dest_key}"] = element["duration"]["value"]
        return combined

maps_service = MapsService()


