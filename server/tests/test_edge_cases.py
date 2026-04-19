import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from utils.config import settings

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def mock_agent_events():
    from services.vector_index import vector_index
    vector_index.mock_events = [
        {"name": "Test Event 1", "topic": "AI", "address": "123 AI Lane"},
        {"name": "Test Event 2", "topic": "Cloud", "address": "456 Cloud Rd"},
        {"name": "Test Event 3", "topic": "Hardware", "address": "789 Chip St"}
    ]
    return vector_index.mock_events

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

async def test_itinerary_ai_quota_fallback(async_client: AsyncClient):
    """Edge Case: AI Quota hit should trigger Resilience Mode (simulated=True)."""
    with patch("services.agent.AgentService.generate_itinerary") as mock_gen:
        # Simulate a timeout or AI failure
        mock_gen.side_effect = Exception("AI Timeout")
        
        payload = {
            "user_location": {"latitude": 37.784261, "longitude": -122.401344},
            "start_time": "10:00 AM",
            "end_time": "06:00 PM",
            "preferred_topics": ["AI"]
        }
        response = await async_client.post("/api/itinerary", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["simulated"] is True
        assert len(data["itinerary"]) > 0

async def test_staff_action_integration_soft_fail(async_client: AsyncClient):
    """
    Edge Case: Secondary integration failure should NOT 
    block the tactical protocol delivery.
    """
    with patch("api.routes.agent_service.generate_staff_protocol") as mock_protocol:
        with patch("api.routes.fb_manager.verify_token") as mock_verify:
            with patch("api.routes.analytics_manager.log_event_anomaly", side_effect=Exception("BigQuery Down")):
                mock_verify.return_value = {"uid": "test"}
                mock_protocol.return_value = MagicMock(protocol="Tactical Move: Alpha", simulated=False)
                
                payload = {"zone_id": "Gate 4", "alert_type": "Crowd Density"}
                headers = {"Authorization": "Bearer VALID_TOKEN"}
                
                response = await async_client.post("/api/staff/zone-action", json=payload, headers=headers)
                
                assert response.status_code == 200
                assert response.json()["protocol"] == "Tactical Move: Alpha"

async def test_simulated_itinerary_no_topic_matches(async_client: AsyncClient):
    """
    Edge Case: Resilience mode fallback when user topics have zero matches.
    """
    from services.agent import agent_service
    constraints = MagicMock()
    constraints.preferred_topics = ["Underwater Basket Weaving"] 
    
    itinerary = await agent_service._generate_simulated_itinerary(constraints, "Clear")
    
    assert itinerary.simulated is True
    assert len(itinerary.itinerary) == 3
