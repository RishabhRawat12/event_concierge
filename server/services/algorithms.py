"""
Tactical routing engine for deterministic crowd orchestration.
Implements a weighted Dijkstra algorithm for conflict-free venue navigation.
"""
import heapq
import math
import hashlib
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import logging

logger = logging.getLogger(__name__)

class DijkstraRouter:
    """Computes optimal pedestrian paths across high-density architectural zones."""

    def __init__(self, events: List[Dict[str, Any]]):
        """
        Initializes the router with a set of candidate events.
        
        Args:
            events: List of event dictionaries containing 'id', 'latitude', and 'longitude'.
        """
        self._events = events
        # Static graph representation: {origin_id: {dest_id: distance_km}}
        self._graph: Dict[str, Dict[str, float]] = self._build_graph()

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates the great-circle distance between two points on Earth.
        Uses the Haversine formula for spherical approximation.
        """
        # Earth's radius in kilometers
        radius = 6371.0 
        
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        alpha = (math.sin(dphi / 2)**2 + 
                 math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2)
        
        return 2 * radius * math.atan2(math.sqrt(alpha), math.sqrt(1 - alpha))

    def _build_graph(self) -> Dict[str, Dict[str, float]]:
        """Constructs a complete mesh graph representing venue spatiality."""
        graph: Dict[str, Dict[str, float]] = {}
        for i, e1 in enumerate(self._events):
            eid1 = e1.get("id", f"e{i}")
            graph[eid1] = {}
            for j, e2 in enumerate(self._events):
                if i == j:
                    continue
                eid2 = e2.get("id", f"e{j}")
                dist = self._haversine(e1["latitude"], e1["longitude"], 
                                      e2["latitude"], e2["longitude"])
                graph[eid1][eid2] = dist
        return graph

    def find_optimal_path(
        self, 
        start_id: str, 
        end_id: str, 
        congestion_map: Optional[Dict[str, float]] = None
    ) -> Tuple[List[str], float]:
        """
        Executes a weighted search with state-aware memoization.
        """
        # Generate a deterministic hash for the congestion state
        congestion_hash = ""
        if congestion_map:
            # Sort keys for deterministic hashing
            state_str = "|".join(f"{k}:{v}" for k, v in sorted(congestion_map.items()))
            congestion_hash = hashlib.blake2b(state_str.encode(), digest_size=8).hexdigest()
        
        return self._find_path_memoized(start_id, end_id, congestion_hash, tuple(sorted(congestion_map.items())) if congestion_map else ())

    @lru_cache(maxsize=1024)
    def _find_path_memoized(
        self, 
        start_id: str, 
        end_id: str, 
        state_hash: str,
        state_tuple: Tuple[Tuple[str, float], ...]
    ) -> Tuple[List[str], float]:
        """Inner Dijkstra implementation wrapped in LRU cache."""
        congestion_map = dict(state_tuple) if state_tuple else None
        if start_id not in self._graph or end_id not in self._graph:
            return [], 0.0

        # Min-heap queue: (cumulative_weight, current_id, path_sequence)
        pq: List[Tuple[float, str, List[str]]] = [(0.0, start_id, [start_id])]
        visited: Dict[str, float] = {}

        while pq:
            cost, current, path = heapq.heappop(pq)
            
            if current == end_id:
                return path, cost
            
            if current in visited and visited[current] <= cost:
                continue
            
            visited[current] = cost

            for neighbor, weight in self._graph[current].items():
                # Apply tactical congestion weighting (Winning Edge pattern)
                penalty = congestion_map.get(neighbor, 1.0) if congestion_map else 1.0
                new_cost = cost + (weight * penalty)
                
                if neighbor not in visited or visited[neighbor] > new_cost:
                    heapq.heappush(pq, (new_cost, neighbor, path + [neighbor]))

        return [], 0.0

