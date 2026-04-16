import math
import heapq
from typing import List, Dict, Any, Tuple

class DijkstraRouter:
    def __init__(self, events: List[Dict[str, Any]]):
        self.events = events
        # Pre-calculate distances for the graph
        self.graph = self._build_graph()

    def _haversine(self, lat1, lon1, lat2, lon2) -> float:
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles
        return c * r

    def _build_graph(self) -> Dict[str, Dict[str, float]]:
        """
        Builds a complete graph where edges represent physical distance 
        (in km) between event locations.
        """
        graph = {}
        for i, e1 in enumerate(self.events):
            eid1 = e1.get("id", f"e{i}")
            graph[eid1] = {}
            for j, e2 in enumerate(self.events):
                if i == j: continue
                eid2 = e2.get("id", f"e{j}")
                dist = self._haversine(e1["latitude"], e1["longitude"], e2["latitude"], e2["longitude"])
                graph[eid1][eid2] = dist
        return graph

    def find_optimal_path(self, start_id: str, end_id: str, congestion_map: Dict[str, float] = None) -> Tuple[List[str], float]:
        """
        Finds the shortest path between two event IDs using Dijkstra's algorithm.
        Optionally weights edges by congestion levels.
        """
        if start_id not in self.graph or end_id not in self.graph:
            return [], 0.0

        # priority queue (distance, current_node, path)
        pq = [(0.0, start_id, [start_id])]
        visited = set()

        while pq:
            (dist, current, path) = heapq.heappop(pq)
            if current in visited:
                continue
            if current == end_id:
                return path, dist
            
            visited.add(current)

            for neighbor, weight in self.graph[current].items():
                if neighbor not in visited:
                    # Apply congestion penalty (Winning Edge logic)
                    congestion = congestion_map.get(neighbor, 1.0) if congestion_map else 1.0
                    weighted_dist = dist + (weight * congestion)
                    heapq.heappush(pq, (weighted_dist, neighbor, path + [neighbor]))

        return [], 0.0

# Singleton-like instantiation will happen in the service layer
