import pytest
import json
from httpx import AsyncClient
from infrastructure.redis import cache

@pytest.mark.asyncio
async def test_redis_pubsub_link(async_client: AsyncClient):
    """Verifies Redis PubSub infrastructure connectivity."""
    await cache.connect()
    res = await cache.publish("test_channel", {"msg": "ready"})
    assert isinstance(res, int)

@pytest.mark.asyncio
async def test_itinerary_arch_layering(async_client: AsyncClient):
    """Verifies Attendee -> Service -> Infrastructure layering."""
    payload = {
        "user_location": {"latitude": 37.7842, "longitude": -122.4013},
        "start_time": "10:00 AM",
        "end_time": "05:00 PM",
        "preferred_topics": ["AI"]
    }
    response = await async_client.post("/api/itinerary", json=payload)
    assert response.status_code == 200
    assert "itinerary" in response.json()

@pytest.mark.asyncio
async def test_security_bearer_enforcement(async_client: AsyncClient):
    """Verifies HTTPBearer standardization."""
    payload = {"zone_id": "Gate 4", "alert_type": "Capacity"}
    response = await async_client.post("/api/staff/zone-action", json=payload)
    assert response.status_code == 403
