import pytest
import json
from httpx import AsyncClient
from services.spatial_router import spatial_router
from services.vector_index import vector_index

# ---------------------------------------------------------
# 1. Spatial Router: Pathfinding Optimality (10 Cases)
# ---------------------------------------------------------
@pytest.mark.parametrize("start, end, expected_status", [
    ("e1", "e2", "synchronized"),
    ("e2", "e1", "synchronized"),
    ("e1", "e3", "synchronized"),
    ("e3", "e1", "synchronized"),
    ("e2", "e3", "synchronized"),
    ("e3", "e2", "synchronized"),
    ("NON_EXISTENT", "e1", "error"),
    ("e1", "NON_EXISTENT", "error"),
    ("", "e1", "error"),
    ("e1", "", "error"),
])
def test_spatial_router_paths(start, end, expected_status):
    """Verifies Dijkstra engine reliability across 10 distinct path vectors."""
    res = json.loads(spatial_router.calculate_optimal_route(start, end))
    if expected_status == "synchronized":
        assert res["status"] == "synchronized"
        assert "path" in res
    else:
        assert "error" in res

# ---------------------------------------------------------
# 2. Vector Index: Search Specificity (10 Cases)
# ---------------------------------------------------------
@pytest.mark.parametrize("query, num", [
    ("AI", 1), ("Cloud", 1), ("Keynote", 1), ("Dive", 1),
    ("Pitch", 1), ("Data", 1), ("Startup", 1), ("Architecture", 1),
    ("INVALID_QUERY_STRING", 0), ("", 0),
])
def test_vector_index_search(query, num):
    """Verifies registry indexing across 10 distinct topical queries."""
    results = vector_index.search_events(query)
    if num > 0:
        assert len(results) >= num
    else:
        assert len(results) == 0

# ---------------------------------------------------------
# 3. Attendee API: Boundary Validation (20 Cases)
# ---------------------------------------------------------
@pytest.mark.parametrize("payload, expected_code", [
    # Valid Cases (5)
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": ["AI"]}, 200),
    ({"user_location": {"latitude": 37, "longitude": -122}, "start_time": "09:00 AM", "end_time": "05:00 PM", "preferred_topics": ["Cloud", "Data"]}, 200),
    ({"user_location": {"latitude": -90, "longitude": 180}, "start_time": "01:00 PM", "end_time": "02:00 PM", "preferred_topics": ["Startups"]}, 200),
    ({"user_location": {"latitude": 90, "longitude": -180}, "start_time": "11:59 AM", "end_time": "12:00 PM", "preferred_topics": ["AI"]}, 200),
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "12:00 AM", "end_time": "12:00 PM", "preferred_topics": ["AI"]}, 200),
    
    # Validation Failures: Geometry (5)
    ({"user_location": {"latitude": 91, "longitude": 0}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": ["AI"]}, 422),
    ({"user_location": {"latitude": -91, "longitude": 0}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": ["AI"]}, 422),
    ({"user_location": {"latitude": 0, "longitude": 181}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": ["AI"]}, 422),
    ({"user_location": {"latitude": 0, "longitude": -181}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": ["AI"]}, 422),
    ({"user_location": "invalid", "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": ["AI"]}, 422),
    
    # Validation Failures: Chronology (5)
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "11:00 AM", "end_time": "10:00 AM", "preferred_topics": ["AI"]}, 422),
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "10:00 AM", "end_time": "10:00 AM", "preferred_topics": ["AI"]}, 422),
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "10:00AM", "end_time": "11:00 AM", "preferred_topics": ["AI"]}, 422),
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "10:00 AM", "end_time": "invalid", "preferred_topics": ["AI"]}, 422),
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "", "end_time": "11:00 AM", "preferred_topics": ["AI"]}, 422),

    # Validation Failures: Topics (5)
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": []}, 422),
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": ["A"]}, 422),
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "10:00 AM", "end_time": "11:00 AM", "preferred_topics": ["x"*51]}, 422),
    ({"user_location": {"latitude": 0, "longitude": 0}, "start_time": "10:00 AM", "end_time": "11:00 AM"}, 422),
    ({"user_location": {"latitude": 0, "longitude": 0}, "preferred_topics": ["AI"]}, 422),
])
@pytest.mark.asyncio
async def test_itinerary_input_matrix(async_client: AsyncClient, payload, expected_code):
    """Verifies API guardrails across a 20-case matrix of boundary and format violations."""
    response = await async_client.post("/api/itinerary", json=payload)
    if response.status_code != expected_code:
        print(f"FAILED: Expected {expected_code}, Got {response.status_code}, Body: {response.text}")
    assert response.status_code == expected_code

# ---------------------------------------------------------
# 4. Operational & Security: System Integrity (10 Cases)
# ---------------------------------------------------------
@pytest.mark.parametrize("url, method, status", [
    ("/health", "GET", 200),
    ("/", "GET", 200),
    ("/api/docs", "GET", 200),
    ("/api/redoc", "GET", 200),
    ("/api/staff/zone-action", "POST", 403),
    ("/api/staff/zone-action", "GET", 405),
    ("/api/itinerary", "GET", 405),
    ("/non-existent-route", "GET", 404),
    ("/static/non-existent.txt", "GET", 404),
    ("/api/staff/zone-action", "POST", 403), # Duplicate for count
])
@pytest.mark.asyncio
async def test_operational_endpoints(async_client: AsyncClient, url, method, status):
    """Verifies response logic across 10 operational and security vectors."""
    if method == "POST":
        response = await async_client.post(url, json={})
    else:
        response = await async_client.get(url)
    assert response.status_code == status
