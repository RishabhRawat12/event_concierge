import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from unittest.mock import patch
from redis.exceptions import RedisError

@pytest.mark.asyncio
async def test_itinerary_validation_error_422():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/itinerary", json={
            "start_time": "09:00 AM",
            "endTime": "05:00 PM",
            "preferred_topics": ["AI"]
        })
    assert response.status_code == 422
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_itinerary_service_unavailable_503():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    with patch("utils.redis.cache.is_rate_limited", side_effect=RedisError("Connection lost")):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/itinerary", json={
                "user_location": {"latitude": 37.7749, "longitude": -122.4194},
                "start_time": "09:00 AM",
                "end_time": "05:00 PM",
                "preferred_topics": ["AI"]
            })
    assert response.status_code == 503
    assert response.json()["error"] == "Service Unavailable"

@pytest.mark.asyncio
async def test_itinerary_internal_error_500():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    with patch("api.routes.weather_service.get_current_weather", side_effect=Exception("Unexpected crash")):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/itinerary", json={
                "user_location": {"latitude": 37.7749, "longitude": -122.4194},
                "start_time": "09:00 AM",
                "end_time": "05:00 PM",
                "preferred_topics": ["AI"]
            })
    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    assert "trace_id" in data

@pytest.mark.asyncio
async def test_staff_action_unauthorized_403():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/staff/zone-action", json={
            "zone_id": "Main Entrance",
            "alert_type": "Emergency"
        }, headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]

@pytest.mark.asyncio
async def test_rate_limiting_staged():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    with patch("utils.redis.cache.is_rate_limited", return_value=True):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/itinerary", json={
                "user_location": {"latitude": 37.7749, "longitude": -122.4194},
                "start_time": "09:00 AM",
                "end_time": "05:00 PM",
                "preferred_topics": ["AI"]
            })
    assert response.status_code == 429
    assert "quota" in response.json()["detail"].lower()


