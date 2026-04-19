"""
Spatial router engine for optimal event pathfinding.
Implements Dijkstra's algorithm for conflict-free itinerary orchestration.
"""
import json
import logging
from typing import Any, Dict, List, Tuple, Optional
from .algorithms import DijkstraRouter

logger = logging.getLogger(__name__)

class SpatialRouterService:
    """Orchestrates deterministic pathfinding for event transitions."""

    def __init__(self) -> None:
        self._router: Optional[DijkstraRouter] = None

    def initialize(self, events: List[Dict[str, Any]]) -> None:
        """Synchronizes the tactical event graph."""
        try:
            self._router = DijkstraRouter(events)
            logger.info("Spatial Router Engine synchronized.")
        except Exception as e:
            logger.error(f"Router initialization failure: {e}")

    def calculate_optimal_route(self, start_event_id: str, end_event_id: str) -> str:
        """Calculates shortest spatial paths between event nodes."""
        if not self._router:
            return json.dumps({"error": "Orchestration state not ready."})
        
        try:
            path, dist = self._router.find_optimal_path(start_event_id, end_event_id)
            return json.dumps({
                "path": path, 
                "total_distance_km": round(dist, 2),
                "status": "synchronized"
            })
        except Exception as e:
            logger.error(f"Pathfinding anomaly: {e}")
            return json.dumps({"error": "Routing failure."})

spatial_router = SpatialRouterService()
