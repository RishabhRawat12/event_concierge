import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from schemas.models import ItineraryResponse, Event

pytestmark = pytest.mark.asyncio

async def test_invalid_coordinates(async_client: AsyncClient):
    payload = {
        "user_location": {"latitude": 95.0, "longitude": 200.0},  # Invalid lat/lng
        "start_time": "10:00 AM",
        "end_time": "2:00 PM",
        "preferred_topics": ["AI"]
    }
    response = await async_client.post("/api/itinerary", json=payload)
    # Pydantic automatically catches the ge/le constraints and throws a 422
    assert response.status_code == 422


@patch('services.maps.maps_service.get_walking_time')
@patch('services.gemini.gemini_service.generate_itinerary')
async def test_successful_itinerary(mock_generate, mock_walking, async_client: AsyncClient):
    # Mock map behavior for the new batched API
    # Return a dictionary that returns 300 seconds for any coordinate combination
    from collections import defaultdict
    mock_walking.return_value = defaultdict(lambda: 300)
    
    # Mock Gemini returned object
    mock_event = Event(
        event_name="AI & Future of Work Keynote",
        start_time="10:00 AM",
        end_time="11:30 AM",
        walking_directions="Head North for 5 mins.",
        transition_time_seconds=300
    )
    mock_generate.return_value = ItineraryResponse(itinerary=[mock_event])
    
    payload = {
        "user_location": {"latitude": 37.784261, "longitude": -122.401344},
        "start_time": "10:00 AM",
        "end_time": "2:00 PM",
        "preferred_topics": ["AI"]
    }
    
    response = await async_client.post("/api/itinerary", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "itinerary" in data
    assert len(data["itinerary"]) == 1
    assert data["itinerary"][0]["event_name"] == "AI & Future of Work Keynote"


@patch('services.maps.MapsService.get_walking_time')
async def test_missing_api_keys(mock_walking, async_client: AsyncClient):
    # If Maps API fails (e.g. missing API key, returning a fallback or throwing RuntimeError)
    mock_walking.side_effect = RuntimeError("Google Maps API failed to return walking time")
    
    payload = {
        "user_location": {"latitude": 37.784261, "longitude": -122.401344},
        "start_time": "10:00 AM",
        "end_time": "2:00 PM",
        "preferred_topics": ["Startups"]
    }
    
    response = await async_client.post("/api/itinerary", json=payload)
    # Expect 502 Bad Gateway for external API failure mapped from RuntimeError
    assert response.status_code == 502


@patch('utils.redis.cache.get')
@patch('utils.redis.cache.set')
@patch('aiohttp.ClientSession.get')
async def test_cache_hit_vs_miss_behavior(mock_session_get, mock_cache_set, mock_cache_get):
    from services.maps import MapsService
    svc = MapsService()
    
    origin = {"latitude": 37.7, "longitude": -122.4}
    destination = {"latitude": 37.8, "longitude": -122.5}
    
    # 1. Test Cache Hit
    mock_cache_get.return_value = "450"  # 450 seconds cached
    hit_result = await svc.get_walking_time(origin, destination)
    
    assert hit_result == 450
    mock_session_get.assert_not_called()  # Maps API should NOT be called
    
    # Reset mocks
    mock_cache_get.reset_mock()
    
    # 2. Test Cache Miss
    mock_cache_get.return_value = None
    
    # Mocking standard Maps Distance Matrix response
    mock_response = AsyncMockResponse(
        status=200, 
        json_data={
            "status": "OK",
            "rows": [{"elements": [{"status": "OK", "duration": {"value": 600}}]}]
        }
    )
    mock_session_get.return_value = mock_response
    
    miss_result = await svc.get_walking_time(origin, destination)
    assert miss_result == 600
    mock_session_get.assert_called_once()
    mock_cache_set.assert_called_once()


class AsyncMockResponse:
    def __init__(self, status, json_data):
        self.status = status
        self._json_data = json_data

    async def json(self):
        return self._json_data

    async def text(self):
        import json
        return json.dumps(self._json_data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
