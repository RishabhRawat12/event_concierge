import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app
from utils.redis import cache

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(autouse=True)
async def reset_singletons():
    # Setup logic if needed
    pass
    yield

@pytest_asyncio.fixture(autouse=True)
async def setup_cache():
    await cache.connect()
    # Create an AsyncMock that returns False
    mock_limit = AsyncMock(return_value=False)
    with patch("utils.redis.cache.is_rate_limited", side_effect=mock_limit):
        yield
        await cache.close()


