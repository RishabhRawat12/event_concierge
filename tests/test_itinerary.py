import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from schemas.models import ItineraryResponse, Event
import json

pytestmark = pytest.mark.asyncio

@pytest.mark.parametrize("payload", [
    {"user_location": {"latitude": 95.0, "longitude": 200.0}, "start_time": "10:00 AM", "end_time": "2:00 PM", "preferred_topics": ["AI"]},
    {"user_location": {"latitude": 40.0, "longitude": 50.0}, "start_time": "10:00 AM", "end_time": "2:00 PM", "preferred_topics": []}, # Empty list 
    {"user_location": {"latitude": 0, "longitude": 0}, "start_time": "1", "end_time": "2:00 PM", "preferred_topics": ["AI"]}, # Too short
    {"user_location": {"latitude": "thirty", "longitude": "forty"}, "start_time": "10:00 AM", "end_time": "02:00 PM", "preferred_topics": ["AI"]}, # Bad types
])
@patch('services.maps.MapsService.get_walking_time')
@patch('services.gemini.GeminiService.generate_itinerary')
async def test_invalid_itinerary_payloads(mock_gen, mock_maps, payload, async_client: AsyncClient):
    response = await async_client.post("/api/itinerary", json=payload)
    assert response.status_code == 422

@patch('services.maps.maps_service.get_walking_time')
@patch('services.gemini.gemini_service.generate_itinerary')
async def test_successful_itinerary(mock_generate, mock_walking, async_client: AsyncClient):
    mock_walking.return_value = {"37.784261,-122.401344|37.784261,-122.401344": 300}
    mock_event = Event(
        event_name="AI & Future of Work Keynote",
        start_time="10:00 AM", end_time="11:30 AM",
        walking_directions="Head North", transition_time_seconds=300
    )
    mock_generate.return_value = ItineraryResponse(itinerary=[mock_event])
    payload = {
        "user_location": {"latitude": 37.784261, "longitude": -122.401344},
        "start_time": "10:00 AM", "end_time": "2:00 PM", "preferred_topics": ["AI"]
    }
    response = await async_client.post("/api/itinerary", json=payload)
    assert response.status_code == 200

@patch('services.maps.googlemaps.Client')
async def test_maps_logic_and_cache(mock_client_class):
    from services.maps import MapsService
    # Ensure cache is mocked or flushed
    mock_client = mock_client_class.return_value
    mock_client.distance_matrix.return_value = {
        "status": "OK",
        "rows": [{"elements": [{"status": "OK", "duration": {"value": 600}}]}]
    }
    svc = MapsService()
    origin = {"latitude": 37.7, "longitude": -122.4}
    destination = {"latitude": 37.8, "longitude": -122.5}
    
    # We use a unique coordinate pair to avoid cache hits from other tests if caching is active
    res = await svc.get_walking_time([origin], [destination])
    assert res["37.7,-122.4|37.8,-122.5"] == 600

@patch('services.maps.googlemaps.Client')
async def test_maps_http_errors(mock_client_class):
    from services.maps import MapsService
    mock_client = mock_client_class.return_value
    mock_client.distance_matrix.return_value = {"status": "REQUEST_DENIED"}
    svc = MapsService()
    origin = {"latitude": 10.0, "longitude": 20.0}
    destination = {"latitude": 11.0, "longitude": 21.0}
    with pytest.raises(RuntimeError):
        await svc.get_walking_time([origin], [destination])
