from http import HTTPStatus

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from taskiq import InMemoryBroker, TaskiqEvents

from rastro.app import create_app
from rastro.common.presentation.dependencies import AppSettings
from rastro.settings import Settings

OPENAPI_PAGES = ["/openapi.json", "/docs", "/redoc"]


@pytest.mark.parametrize("openapi_enabled", [True])
@pytest.mark.parametrize("path", OPENAPI_PAGES)
async def test_the_openapi_pages_answer_when_the_setting_is_on(
    openapi_client: httpx.AsyncClient, path: str
) -> None:
    response = await openapi_client.get(path)

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize("openapi_enabled", [False])
@pytest.mark.parametrize("path", OPENAPI_PAGES)
async def test_the_openapi_pages_are_not_found_when_the_setting_is_off(
    openapi_client: httpx.AsyncClient, path: str
) -> None:
    response = await openapi_client.get(path)

    assert response.json() == {"type": "request.not_found", "status": 404}


async def test_the_openapi_schema_is_not_found_without_its_variable(
    postgres_url_only: None,
) -> None:
    app = create_app(
        settings=Settings(), sessionmaker=async_sessionmaker(), broker=InMemoryBroker()
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://testserver"
    ) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == HTTPStatus.NOT_FOUND


async def test_the_settings_dependency_returns_the_settings_of_the_app(
    settings: Settings,
) -> None:
    app = create_app(
        settings=settings, sessionmaker=async_sessionmaker(), broker=InMemoryBroker()
    )
    received: list[Settings] = []

    @app.get("/settings")
    def read_settings(app_settings: AppSettings) -> None:
        received.append(app_settings)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://testserver"
    ) as client:
        await client.get("/settings")

    assert received[0] is settings


async def test_the_app_starts_its_broker_and_shuts_it_down(settings: Settings) -> None:
    broker = InMemoryBroker()
    events: list[str] = []
    broker.add_event_handler(
        TaskiqEvents.CLIENT_STARTUP, lambda _state: events.append("startup")
    )
    broker.add_event_handler(
        TaskiqEvents.CLIENT_SHUTDOWN, lambda _state: events.append("shutdown")
    )
    app = create_app(
        settings=settings, sessionmaker=async_sessionmaker(), broker=broker
    )

    async with app.router.lifespan_context(app):
        assert events == ["startup"]

    assert events == ["startup", "shutdown"]
