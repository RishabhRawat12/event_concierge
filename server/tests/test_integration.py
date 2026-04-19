import pytest
import pytest_asyncio
import json
from httpx import AsyncClient
from infrastructure.redis import cache

@pytest.mark.asyncio
async def test_redis_connectivity():
    """Verifies infrastructure link for Redis Pub/Sub."""
    await cache.connect()
    res = await cache.publish("heartbeat", {"status": "ok"})
    assert isinstance(res, (int, float))

@pytest.mark.asyncio
async def test_itinerary_schema_validation(async_client: AsyncClient):
    """Verifies Pydantic V2 enforcement on the itinerary endpoint."""
    cases = [
        # Invalid Latitude
        {"user_location": {"latitude": 100, "longitude": 0}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": ["AI"]},
        # Invalid Time Sequence
        {"user_location": {"latitude": 0, "longitude": 0}, "start_time": "12:00 PM", "end_time": "10:00 AM", "preferred_topics": ["AI"]},
        # Empty Topics
        {"user_location": {"latitude": 0, "longitude": 0}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": []},
    ]
    for case in cases:
        response = await async_client.post("/api/itinerary", json=case)
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_itinerary_success_path(async_client: AsyncClient):
    """Verifies business logic layering and serialization integrity."""
    payload = {
        "user_location": {"latitude": 37.7842, "longitude": -122.4013},
        "start_time": "10:00 AM",
        "end_time": "05:00 PM",
        "preferred_topics": ["AI", "Cloud"]
    }
    response = await async_client.post("/api/itinerary", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "itinerary" in data
    assert "current_weather" in data
    assert isinstance(data["simulated"], bool)

@pytest.mark.asyncio
async def test_staff_unauthorized_access(async_client: AsyncClient):
    """Verifies standard HTTPBearer enforcement on privileged routes."""
    response = await async_client.post("/api/staff/zone-action", json={"zone_id": "A", "alert_type": "Density"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Verifies basic system availability."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
