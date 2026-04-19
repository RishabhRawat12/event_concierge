import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from schemas.models import StaffActionResponse
from unittest.mock import patch, AsyncMock
from utils.config import settings

@pytest.mark.asyncio
@patch("api.routes.agent_service.generate_staff_protocol")
@patch("api.routes.fb_manager.verify_token")
@patch("api.routes.fb_manager.update_zone_status", new_callable=AsyncMock)
@patch("api.routes.analytics_manager.log_event_anomaly", new_callable=AsyncMock)
@patch("api.routes.ws_manager.broadcast", new_callable=AsyncMock)
async def test_staff_zone_action_endpoint_authorized(
    mock_ws, mock_analytics, mock_fb_update, mock_verify, mock_protocol, async_client: AsyncClient
):
    # Mocking verify_token to return a valid user payload
    mock_verify.return_value = {"uid": "test_user", "email": "staff@event.com"}
    
    # Mocking the agent service to avoid external API calls
    mock_response = StaffActionResponse(protocol="Engage crowd control barriers.")
    mock_protocol.return_value = mock_response
    
    payload = {"zone_id": "Gate 4", "alert_type": "Crowd Density"}
    headers = {"Authorization": "Bearer VALID_MOCK_TOKEN"}
    
    response = await async_client.post("/api/staff/zone-action", json=payload, headers=headers)
        
    assert response.status_code == 200
    expected_data = response.json()
    assert expected_data["protocol"] == "Engage crowd control barriers."
    
    # Verify the side effects happened
    mock_fb_update.assert_called_once()
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
        
        # We don't necessarily need to test "WRONG_TOKEN" here if verify_token is properly mocked to fail
        # but the current implementation of verify_token will throw ValueError on invalid token.
