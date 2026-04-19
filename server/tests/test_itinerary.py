import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from schemas.models import ItineraryResponse, Event

pytestmark = pytest.mark.asyncio

@pytest.mark.parametrize("payload", [
    {"user_location": {"latitude": 95.0, "longitude": 200.0}, "start_time": "10:00 AM", "end_time": "2:00 PM", "preferred_topics": ["AI"]},
    {"user_location": {"latitude": 40.0, "longitude": 50.0}, "start_time": "10:00 AM", "end_time": "2:00 PM", "preferred_topics": []}, # Empty list 
    {"user_location": {"latitude": 0, "longitude": 0}, "start_time": "1", "end_time": "2:00 PM", "preferred_topics": ["AI"]}, # Too short
])
@patch('services.agent.AgentService.generate_itinerary')
async def test_invalid_itinerary_payloads(mock_gen, payload, async_client: AsyncClient):
    response = await async_client.post("/api/itinerary", json=payload)
    assert response.status_code == 422

@patch('services.agent.agent_service.generate_itinerary')
async def test_successful_itinerary(mock_generate, async_client: AsyncClient):
    mock_event = Event(
        event_name="AI & Future of Work Keynote",
        start_time="10:00 AM", end_time="11:30 AM",
        walking_directions="Head North", transition_time_seconds=300
    )
    mock_generate.return_value = ItineraryResponse(itinerary=[mock_event], current_weather="Clear")
    payload = {
        "user_location": {"latitude": 37.784261, "longitude": -122.401344},
        "start_time": "10:00 AM", 
        "end_time": "06:00 PM", 
        "preferred_topics": ["AI"]
    }
    response = await async_client.post("/api/itinerary", json=payload)
    assert response.status_code == 200

@patch('httpx.AsyncClient.get')
async def test_maps_logic_httpx(mock_get):
    from services.maps import maps_service
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "OK",
        "rows": [{"elements": [{"status": "OK", "duration": {"value": 600}}]}]
    }
    mock_get.return_value = mock_response
    
    origin = {"latitude": 37.7, "longitude": -122.4}
    destination = {"latitude": 37.8, "longitude": -122.5}
    
    res = await maps_service._fetch_matrix_httpx([origin], [destination])
    assert res["37.7,-122.4|37.8,-122.5"] == 600
