import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from utils.redis import cache
from unittest.mock import patch

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(autouse=True)
async def disable_rate_limiting():
    with patch("utils.redis.cache.is_rate_limited", return_value=False):
        yield

@pytest_asyncio.fixture(autouse=True)
async def reset_singletons():
    from services.maps import maps_service
    maps_service._client = None
    yield

@pytest_asyncio.fixture(autouse=True)
async def setup_cache():
    await cache.connect()
    yield
    await cache.close()


