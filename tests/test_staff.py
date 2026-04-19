import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from schemas.models import StaffActionResponse
from unittest.mock import patch, AsyncMock
from utils.config import settings

@pytest.mark.asyncio
@patch("api.routes.gemini_service.generate_staff_protocol")
@patch("api.routes.fb_manager.update_zone_status", new_callable=AsyncMock)
@patch("api.routes.analytics_manager.log_event_anomaly", new_callable=AsyncMock)
@patch("api.routes.ws_manager.broadcast", new_callable=AsyncMock)
async def test_staff_zone_action_endpoint_authorized(
    mock_ws, mock_analytics, mock_fb, mock_protocol, async_client: AsyncClient
):
    # Mocking the gemini service to avoid external API calls during testing
    mock_response = StaffActionResponse(protocol="Engage crowd control barriers.")
    mock_protocol.return_value = mock_response
    
    payload = {"zone_id": "Gate 4", "alert_type": "Crowd Density"}
    # Use the token from settings to ensure match
    headers = {"Authorization": f"Bearer {settings.STAFF_SECRET_TOKEN}"}
    
    response = await async_client.post("/api/staff/zone-action", json=payload, headers=headers)
        
    assert response.status_code == 200
    expected_data = response.json()
    assert expected_data["protocol"] == "Engage crowd control barriers."
    
    # Verify the "Winning Edge" side effects happened
    mock_fb.assert_called_once()
    mock_analytics.assert_called_once()
    mock_ws.assert_called_once()

@pytest.mark.asyncio
async def test_staff_zone_action_endpoint_unauthorized():
    payload = {"zone_id": "Zone B", "alert_type": "Crowd Density"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # No header
        response = await ac.post("/api/staff/zone-action", json=payload)
        assert response.status_code == 403
        
        # Wrong header
        headers = {"Authorization": "Bearer WRONG_TOKEN"}
        response = await ac.post("/api/staff/zone-action", json=payload, headers=headers)
        assert response.status_code == 403
