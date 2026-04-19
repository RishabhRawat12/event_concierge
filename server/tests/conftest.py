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
    await cache.connect()
    fb_manager.connect()
    yield
    await cache.close()
