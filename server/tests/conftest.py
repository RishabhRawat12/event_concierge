import pytest_asyncio
import os
from httpx import AsyncClient, ASGITransport
from main import app
from infrastructure.redis import cache
from infrastructure.firebase import fb_manager

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(autouse=True)
async def setup_infrastructure():
    """Real Infrastructure Integration."""
    from services.vector_index import vector_index
    from services.spatial_router import spatial_router
    
    await cache.connect()
    # Comprehensive state reset (Winner Tier Resilience)
    await cache.clear()
    fb_manager.connect()
    
    # Initialize services
    events = await vector_index.load_events()
    spatial_router.initialize(events)
    
    yield
    await cache.close()
