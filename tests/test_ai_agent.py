import pytest
from services.gemini import GeminiService
from utils.algorithms import DijkstraRouter
import json

@pytest.mark.asyncio
async def test_calculate_optimal_route_tool():
    svc = GeminiService()
    # Mocking the router directly to avoid file I/O dependency
    mock_events = [
        {"id": "e1", "latitude": 37.784261, "longitude": -122.401344},
        {"id": "e2", "latitude": 37.784860, "longitude": -122.400249}
    ]
    svc.router = DijkstraRouter(mock_events)
    
    # Manually invoke the tool
    result_json = svc.calculate_optimal_route("e1", "e2")
    result = json.loads(result_json)
    
    assert "path" in result
    assert result["path"] == ["e1", "e2"]
    assert result["total_distance_km"] > 0

@pytest.mark.asyncio
async def test_get_zone_congestion_tool():
    svc = GeminiService()
    result_json = svc.get_zone_congestion("Main Entrance")
    result = json.loads(result_json)
    
    assert result["zone_id"] == "Main Entrance"
    assert "status" in result
    assert result["status"] == "MODERATE"

@pytest.mark.asyncio
async def test_agentic_load_events():
    svc = GeminiService()
    await svc.load_events()
    assert len(svc.mock_events) > 0
    assert svc.router is not None
