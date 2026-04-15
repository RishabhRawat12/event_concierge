import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from schemas.models import StaffActionResponse

@pytest.mark.asyncio
async def test_staff_zone_action_endpoint_authorized(mocker):
    # Mocking the gemini service to avoid external API calls during testing
    mock_response = StaffActionResponse(protocol="Engage crowd control barriers and notify manager.")
    mocker.patch("api.routes.gemini_service.generate_staff_protocol", return_value=mock_response)
    
    payload = {"zone_id": "Zone B", "alert_type": "Crowd Density"}
    headers = {"Authorization": "Bearer SUPER_SECRET_STAFF_TOKEN"}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/staff/zone-action", json=payload, headers=headers)
        
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
        assert response.status_code == 403
        
        # Wrong header
        headers = {"Authorization": "Bearer WRONG"}
        response = await ac.post("/api/staff/zone-action", json=payload, headers=headers)
        assert response.status_code == 403
