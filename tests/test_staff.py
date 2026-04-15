import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from schemas.models import StaffActionResponse
from unittest.mock import patch

@pytest.mark.asyncio
@patch("api.routes.gemini_service.generate_staff_protocol")
async def test_staff_zone_action_endpoint_authorized(mock_protocol, async_client: AsyncClient):
    # Mocking the gemini service to avoid external API calls during testing
    mock_response = StaffActionResponse(protocol="Engage crowd control barriers and notify manager.")
    mock_protocol.return_value = mock_response
    
    payload = {"zone_id": "Zone B", "alert_type": "Crowd Density"}
    headers = {"Authorization": "Bearer SUPER_SECRET_STAFF_TOKEN"}
    
    response = await async_client.post("/api/staff/zone-action", json=payload, headers=headers)
        
    assert response.status_code == 200
    data = response.json()
    assert "protocol" in data

@pytest.mark.asyncio
async def test_staff_zone_action_endpoint_unauthorized():
    payload = {"zone_id": "Zone B", "alert_type": "Crowd Density"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # No header
        response = await ac.post("/api/staff/zone-action", json=payload)
        assert response.status_code == 401
        
        # Wrong header (FastAPI HTTPBearer doesn't validate content automatically, just presence)
        # Actually, for 100% security logic, I added a verify function that raises 403 for wrong token.
        # But if the header is missing, it's 401.
        headers = {"Authorization": "Bearer WRONG"}
        response = await ac.post("/api/staff/zone-action", json=payload, headers=headers)
        assert response.status_code == 403
