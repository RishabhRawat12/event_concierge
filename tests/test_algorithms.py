import pytest
from utils.algorithms import DijkstraRouter

def test_haversine_accuracy():
    router = DijkstraRouter([])
    # Dist between these two points is approx 0.13 km
    dist = router._haversine(37.784261, -122.401344, 37.784860, -122.400249)
    assert 0.1 < dist < 0.2

def test_dijkstra_shortest_path():
    events = [
        {"id": "A", "latitude": 0, "longitude": 0},
        {"id": "B", "latitude": 1, "longitude": 0},
        {"id": "C", "latitude": 0, "longitude": 1},
        {"id": "D", "latitude": 1, "longitude": 1}
    ]
    router = DijkstraRouter(events)
    # Direct path A to B
    path, dist = router.find_optimal_path("A", "B")
    assert path == ["A", "B"]
    assert dist > 0

def test_dijkstra_congestion_penalty():
    events = [
        {"id": "Start", "latitude": 0, "longitude": 0},
        {"id": "FastPath", "latitude": 0.5, "longitude": 0.5},
        {"id": "SlowPath", "latitude": 0.1, "longitude": 0.1},
        {"id": "End", "latitude": 1, "longitude": 1}
    ]
    router = DijkstraRouter(events)
    congestion_map = {"SlowPath": 10.0} # Massive penalty
    
    path, dist = router.find_optimal_path("Start", "End", congestion_map=congestion_map)
    # Should avoid SlowPath now
    assert "SlowPath" not in path

def test_invalid_nodes():
    router = DijkstraRouter([])
    path, dist = router.find_optimal_path("X", "Y")
    assert path == []
    assert dist == 0.0
