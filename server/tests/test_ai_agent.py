import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from services.agent import AgentService
from services.spatial_router import spatial_router
from services.vector_index import vector_index

@pytest.fixture(autouse=True)
def mock_vertex():
    with patch("vertexai.init"), \
         patch("vertexai.generative_models.GenerativeModel") as mock_model:
        yield mock_model

@pytest.mark.asyncio
async def test_agent_get_zone_congestion():
    svc = AgentService()
    # Mock firebase manager response
    with patch("services.agent.fb_manager.get_zone_status", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"status": "CRITICAL", "congestion": 85}
        result_json = await svc.get_zone_congestion("Main Entrance")
        result = json.loads(result_json)
        
        assert result["zone_id"] == "Main Entrance"
        assert result["status"] == "CRITICAL"
        assert result["congestion_level"] == 85

@pytest.mark.asyncio
async def test_spatial_router_init():
    mock_events = [
        {"id": "e1", "latitude": 37.784261, "longitude": -122.401344, "name": "Event 1", "topic": "AI", "address": "Addr 1"},
        {"id": "e2", "latitude": 37.784860, "longitude": -122.400249, "name": "Event 2", "topic": "Cloud", "address": "Addr 2"}
    ]
    spatial_router.initialize(mock_events)
    result_json = spatial_router.calculate_optimal_route("e1", "e2")
    result = json.loads(result_json)
    
    assert result["status"] == "synchronized"
    assert "path" in result
    assert result["path"] == ["e1", "e2"]

@pytest.mark.asyncio
async def test_vector_index_search():
    mock_events = [
        {"id": "e1", "name": "AI Workshop", "topic": "Artificial Intelligence"},
        {"id": "e2", "name": "Cloud Native", "topic": "Infrastructure"}
    ]
    vector_index.mock_events = mock_events
    
    # Re-indexing
    vector_index._exact_index = {}
    vector_index._token_index = {}
    for i, event in enumerate(mock_events):
        vector_index._exact_index[event["name"].lower()] = [event]
        vector_index._exact_index[event["topic"].lower()] = [event]
    
    results = vector_index.search_events("AI Workshop")
    assert len(results) > 0
    assert results[0]["id"] == "e1"
