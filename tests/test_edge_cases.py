import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from utils.config import settings

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def mock_gemini_events():
    from services.gemini import gemini_service
    # Provide a few dummy events for the simulated engine to pick up
    gemini_service._mock_events = [
        {"name": "Test Event 1", "topic": "AI", "address": "123 AI Lane"},
        {"name": "Test Event 2", "topic": "Cloud", "address": "456 Cloud Rd"},
        {"name": "Test Event 3", "topic": "Hardware", "address": "789 Chip St"}
    ]
    return gemini_service._mock_events

async def test_itinerary_time_inversion(async_client: AsyncClient):
    """Edge Case: Start time after End time should be rejected."""
    payload = {
        "user_location": {"latitude": 37.784261, "longitude": -122.401344},
        "start_time": "05:00 PM",
        "end_time": "10:00 AM",
        "preferred_topics": ["AI"]
    }
    response = await async_client.post("/api/itinerary", json=payload)
    assert response.status_code == 422
    assert "start_time" in response.text.lower()

async def test_itinerary_ai_quota_fallback(async_client: AsyncClient):
    """Edge Case: AI Quota hit (429) should trigger Resilience Mode (simulated=True)."""
    with patch("services.gemini.genai.Client.aio") as mock_gen:
        # Simulate a 429 RESOURCE_EXHAUSTED error
        mock_gen.chats.create.side_effect = Exception("429 RESOURCE_EXHAUSTED")
        
        payload = {
            "user_location": {"latitude": 37.784261, "longitude": -122.401344},
            "start_time": "10:00 AM",
            "end_time": "02:00 PM",
            "preferred_topics": ["AI"]
        }
        response = await async_client.post("/api/itinerary", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["simulated"] is True
        assert len(data["itinerary"]) > 0

async def test_staff_action_integration_soft_fail(async_client: AsyncClient):
    """
    Edge Case: Secondary integration failure (BigQuery) should NOT 
    block the tactical protocol delivery.
    """
    with patch("api.routes.gemini_service.generate_staff_protocol") as mock_protocol:
        with patch("api.routes.analytics_manager.log_event_anomaly", side_effect=Exception("BigQuery Down")):
            mock_protocol.return_value = MagicMock(protocol="Tactical Move: Alpha", simulated=False)
            
            payload = {"zone_id": "Gate 4", "alert_type": "Crowd Density"}
            headers = {"Authorization": f"Bearer {settings.STAFF_SECRET_TOKEN}"}
            
            response = await async_client.post("/api/staff/zone-action", json=payload, headers=headers)
            
            # Should still be 200 despite BigQuery failure
            assert response.status_code == 200
            assert response.json()["protocol"] == "Tactical Move: Alpha"

async def test_simulated_itinerary_no_topic_matches(async_client: AsyncClient):
    """
    Edge Case: Resilience mode fallback when user topics have zero matches
    in the event list. Should return a default schedule instead of failing.
    """
    from services.gemini import gemini_service
    constraints = MagicMock()
    constraints.preferred_topics = ["Underwater Basket Weaving"] # No match
    
    itinerary = await gemini_service._generate_simulated_itinerary(constraints, "Clear")
    
    assert itinerary.simulated is True
    assert len(itinerary.itinerary) == 3
    assert any(p in itinerary.itinerary[0].walking_directions for p in ["AI-Orchestrated:", "Spatial-Path:", "Smart-Flow:"])
