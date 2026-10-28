from http import HTTPStatus

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from taskiq import InMemoryBroker, TaskiqEvents

from rastro.app import create_app
from rastro.common.presentation.dependencies import AppSettings
from rastro.settings import CorsOrigin, Settings

OPENAPI_PAGES = ["/openapi.json", "/docs", "/redoc"]
FRONTEND_ORIGIN = "http://localhost:5173"
OTHER_ORIGIN = "https://other.example"
FRAME_HEADERS = {
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}


def _preflight_headers(*, origin: str, header: str) -> dict[str, str]:
    return {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": f"content-type,{header}",
    }


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


@pytest.mark.parametrize("cors_allowed_origins", [[CorsOrigin(FRONTEND_ORIGIN)]])
async def test_a_preflight_from_an_allowed_origin_allows_credentials_and_the_csrf_header(
    cors_client: httpx.AsyncClient, settings: Settings
) -> None:
    response = await cors_client.options(
        "/api/v1/auth/session",
        headers=_preflight_headers(
            origin=FRONTEND_ORIGIN, header=settings.csrf_header_name
        ),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "X-CSRF-Token" in response.headers["access-control-allow-headers"]


@pytest.mark.parametrize(
    "cors_allowed_origins", [[CorsOrigin("HTTP://LOCALHOST:5173")]]
)
async def test_a_preflight_matches_an_origin_that_the_settings_write_in_uppercase(
    cors_client: httpx.AsyncClient, settings: Settings
) -> None:
    response = await cors_client.options(
        "/api/v1/auth/session",
        headers=_preflight_headers(
            origin=FRONTEND_ORIGIN, header=settings.csrf_header_name
        ),
    )

    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


async def test_a_preflight_allows_a_csrf_header_renamed_by_the_settings(
    settings: Settings,
) -> None:
    app = create_app(
        settings=settings.model_copy(
            update={
                "cors_allowed_origins": [CorsOrigin(FRONTEND_ORIGIN)],
                "csrf_header_name": "X-Paint-Token",
            }
        ),
        sessionmaker=async_sessionmaker(),
        broker=InMemoryBroker(),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://testserver"
    ) as client:
        response = await client.options(
            "/api/v1/auth/session",
            headers=_preflight_headers(origin=FRONTEND_ORIGIN, header="X-Paint-Token"),
        )

    assert response.status_code == HTTPStatus.OK
    assert "X-Paint-Token" in response.headers["access-control-allow-headers"]


@pytest.mark.parametrize("cors_allowed_origins", [[CorsOrigin(FRONTEND_ORIGIN)]])
async def test_a_request_from_an_origin_outside_the_list_gets_no_cors_origin(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.get(
        "/api/v1/security/csrf", headers={"Origin": OTHER_ORIGIN}
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [
        ("GET", "/api/v1/security/csrf", HTTPStatus.NO_CONTENT),
        ("POST", "/api/v1/auth/session/end", HTTPStatus.FORBIDDEN),
        ("GET", "/api/v1/missing", HTTPStatus.NOT_FOUND),
    ],
)
async def test_every_response_blocks_frames(
    client: httpx.AsyncClient,
    settings: Settings,
    method: str,
    path: str,
    status: HTTPStatus,
) -> None:
    del client.headers[settings.csrf_header_name]

    response = await client.request(method, path)

    assert response.status_code == status
    assert {name: response.headers.get(name) for name in FRAME_HEADERS} == FRAME_HEADERS
