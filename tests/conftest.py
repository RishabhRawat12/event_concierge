import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from utils.redis import cache

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture(autouse=True)
async def setup_cache():
    await cache.connect()
    yield
    await cache.close()
