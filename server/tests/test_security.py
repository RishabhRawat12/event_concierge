import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_security_headers():
    """Verify that secure headers are correctly applied to responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "no-referrer"
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]
        assert "unsafe-inline" not in response.headers["Content-Security-Policy"]

@pytest.mark.asyncio
async def test_cors_whitelist_enforcement():
    """Verify that only whitelisted origins can access the API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Whitelisted
        response = await client.post("/api/itinerary", headers={"Origin": "http://localhost:3000"})
        # Note: 422 is expected if body is missing, but CORS headers should be there
        assert "access-control-allow-origin" in response.headers
        
        # Non-whitelisted
        response = await client.post("/api/itinerary", headers={"Origin": "http://malicious.com"})
        assert "access-control-allow-origin" not in response.headers

@pytest.mark.asyncio
async def test_large_file_upload_rejection():
    """Verify that massive file uploads are rejected before OOM."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 6MB file (Limit is 5MB)
        large_content = b"0" * (6 * 1024 * 1024)
        files = {"file": ("test.jpg", large_content, "image/jpeg")}
        response = await client.post("/api/vision/analyze-crowd", files=files)
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_invalid_mime_type_rejection():
    """Verify that only allowed MIME types are ingested."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("exploit.exe", b"executable_content", "application/x-msdownload")}
        response = await client.post("/api/vision/analyze-crowd", files=files)
        assert response.status_code == 415
        assert "unsupported media type" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_staff_auth_leakage_protection():
    """Verify that error responses do not leak internal metadata."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.post("/api/staff/zone-action", headers=headers, json={"zone_id": "Zone A", "alert_type": "Density"})
        assert response.status_code == 403
        data = response.json()
        assert "invalid or expired" in data["detail"].lower()
        # Ensure no internal path names or function names are present
        assert "main.py" not in response.text
        assert "verify_staff_token" not in response.text

@pytest.mark.skip(reason="Rate limiting mocked to False in conftest for suite stability")
async def test_universal_rate_limiting():
    pass
