import os
from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from taskiq import InMemoryBroker

from rastro.app import create_app
from rastro.common.domain.value_objects import CorsOrigin
from rastro.settings import Settings

POSTGRES_URL = "postgresql+psycopg://postgres:hunter2-secret@localhost:5432/postgres"


@pytest.fixture
def empty_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in os.environ:
        if name.startswith("RASTRO_"):
            monkeypatch.delenv(name)


@pytest.fixture
def postgres_url_only(empty_environment: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RASTRO_POSTGRES_URL", POSTGRES_URL)


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


@pytest.fixture
async def cors_client(
    settings: Settings, cors_allowed_origins: list[CorsOrigin]
) -> AsyncIterator[httpx.AsyncClient]:
    """A client of an app whose test parametrizes `cors_allowed_origins`."""
    app = create_app(
        settings=settings.model_copy(
            update={"cors_allowed_origins": cors_allowed_origins}
        ),
        sessionmaker=async_sessionmaker(),
        broker=InMemoryBroker(),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://testserver"
    ) as client:
        yield client
