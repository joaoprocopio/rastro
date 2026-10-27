from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from taskiq import InMemoryBroker

from rastro.app import create_app
from rastro.settings import Settings


@pytest.fixture
async def openapi_client(
    settings: Settings, openapi_enabled: bool
) -> AsyncIterator[httpx.AsyncClient]:
    """A client of an app whose test parametrizes `openapi_enabled`."""
    app = create_app(
        settings=settings.model_copy(update={"openapi_enabled": openapi_enabled}),
        sessionmaker=async_sessionmaker(),
        broker=InMemoryBroker(),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://testserver"
    ) as client:
        yield client
