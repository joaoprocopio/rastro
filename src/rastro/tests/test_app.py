from http import HTTPStatus

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from taskiq import InMemoryBroker, TaskiqEvents

from rastro.app import create_app
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
