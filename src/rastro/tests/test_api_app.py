import os
import subprocess
import sys
from datetime import timedelta
from http import HTTPStatus

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from rastro.api_app import create_api_app
from rastro.common.presentation.dependencies import AppSettings
from rastro.settings import CorsOrigin, Settings
from rastro.tests.conftest import POSTGRES_URL

# Each process binds its tasks once, so this script runs in its own process.
DEFER_SCRIPT = """
import rastro.api
from rastro.auth.presentation.tasks import password_reset_send_task

password_reset_send_task.configure()
print(password_reset_send_task.name)
"""
OPENAPI_PAGES = ["/openapi.json", "/docs", "/redoc"]
SESSION_PATH = "/api/v1/auth/session"
CSRF_PATH = "/api/v1/security/csrf"
CSRF_HEADER = "X-CSRF-Token"
FRONTEND_ORIGIN = "http://localhost:5173"
OTHER_ORIGIN = "https://other.example"
FRONTEND_ORIGINS = [CorsOrigin(FRONTEND_ORIGIN)]
EXAMPLE_SUBDOMAINS = r"https://[a-z]+\.example\.com"
FRAME_HEADERS = {
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}


def test_the_api_process_binds_each_task_under_the_name_that_the_worker_reads() -> None:
    kept = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("OTEL_", "RASTRO_"))
    }

    result = subprocess.run(
        [sys.executable, "-c", DEFER_SCRIPT],
        env={**kept, "RASTRO_POSTGRES_URL": POSTGRES_URL},
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == (
        "auth:rastro.auth.presentation.tasks.password_reset_send_task"
    )


def _preflight_headers(
    *, origin: str, method: str = "POST", header: str
) -> dict[str, str]:
    return {
        "Origin": origin,
        "Access-Control-Request-Method": method,
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
    app = create_api_app(settings=Settings(), sessionmaker=async_sessionmaker())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://testserver"
    ) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == HTTPStatus.NOT_FOUND


async def test_the_settings_dependency_returns_the_settings_of_the_app(
    settings: Settings,
) -> None:
    app = create_api_app(settings=settings, sessionmaker=async_sessionmaker())
    received: list[Settings] = []

    @app.get("/settings")
    def read_settings(app_settings: AppSettings) -> None:
        received.append(app_settings)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://testserver"
    ) as client:
        await client.get("/settings")

    assert received[0] is settings


@pytest.mark.parametrize("cors_settings", [{"cors_allowed_origins": FRONTEND_ORIGINS}])
async def test_a_preflight_with_the_default_settings_allows_a_delete_with_the_csrf_header(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers=_preflight_headers(
            origin=FRONTEND_ORIGIN, method="DELETE", header=CSRF_HEADER
        ),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert response.headers["access-control-allow-methods"] == (
        "DELETE, GET, OPTIONS, PATCH, POST, PUT"
    )
    assert CSRF_HEADER.lower() in response.headers["access-control-allow-headers"]
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers["access-control-max-age"] == "600"


@pytest.mark.parametrize(
    "cors_settings", [{"cors_allowed_origins": [CorsOrigin("HTTP://LOCALHOST:5173")]}]
)
async def test_a_preflight_matches_an_origin_that_the_settings_write_in_uppercase(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers=_preflight_headers(origin=FRONTEND_ORIGIN, header=CSRF_HEADER),
    )

    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


@pytest.mark.parametrize(
    "cors_settings",
    [{"cors_allowed_origins": FRONTEND_ORIGINS, "csrf_header_name": "X-Other"}],
)
async def test_a_preflight_with_the_default_headers_rejects_a_renamed_csrf_header(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers=_preflight_headers(origin=FRONTEND_ORIGIN, header="X-Other"),
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "x-other" not in response.headers["access-control-allow-headers"].lower()


@pytest.mark.parametrize(
    "cors_settings", [{"cors_allowed_origin_regex": EXAMPLE_SUBDOMAINS}]
)
async def test_a_preflight_from_an_origin_that_a_regex_matches_allows_the_origin(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers=_preflight_headers(
            origin="https://app.example.com", header=CSRF_HEADER
        ),
    )

    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


@pytest.mark.parametrize(
    "cors_settings",
    [{"cors_allowed_origin_regex": r"(?i)https://APP\.example\.com"}],
)
async def test_a_preflight_from_an_origin_that_a_regex_with_a_flag_matches_allows_it(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers=_preflight_headers(
            origin="https://app.example.com", header=CSRF_HEADER
        ),
    )

    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


@pytest.mark.parametrize(
    "cors_settings", [{"cors_allowed_origin_regex": EXAMPLE_SUBDOMAINS}]
)
async def test_a_preflight_from_an_origin_that_no_regex_matches_gets_no_cors_origin(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers=_preflight_headers(origin="https://example.org", header=CSRF_HEADER),
    )

    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "cors_settings",
    [
        {
            "cors_allowed_origins": FRONTEND_ORIGINS,
            "cors_allow_methods": ["*"],
            "cors_allow_headers": ["*"],
        }
    ],
)
async def test_a_preflight_with_wildcard_methods_and_headers_allows_any_of_them(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers=_preflight_headers(
            origin=FRONTEND_ORIGIN, method="HEAD", header="X-Anything"
        ),
    )

    assert response.status_code == HTTPStatus.OK
    assert "HEAD" in response.headers["access-control-allow-methods"]
    assert "X-Anything" in response.headers["access-control-allow-headers"]


@pytest.mark.parametrize(
    "cors_settings",
    [
        {
            "cors_allowed_origins": FRONTEND_ORIGINS,
            "cors_expose_headers": ["X-Request-Id"],
        }
    ],
)
async def test_a_request_from_an_allowed_origin_exposes_the_headers_of_the_settings(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.get(CSRF_PATH, headers={"Origin": FRONTEND_ORIGIN})

    assert response.headers["access-control-expose-headers"] == "X-Request-Id"


@pytest.mark.parametrize(
    "cors_settings",
    [
        {
            "cors_allowed_origins": FRONTEND_ORIGINS,
            "cors_preflight_max_age": timedelta(hours=1),
        }
    ],
)
async def test_a_preflight_carries_the_max_age_of_the_settings_in_seconds(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers=_preflight_headers(origin=FRONTEND_ORIGIN, header=CSRF_HEADER),
    )

    assert response.headers["access-control-max-age"] == "3600"


@pytest.mark.parametrize(
    "cors_settings",
    [{"cors_allowed_origins": FRONTEND_ORIGINS, "cors_allow_credentials": False}],
)
async def test_a_preflight_without_the_credentials_flag_allows_no_credentials(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers=_preflight_headers(origin=FRONTEND_ORIGIN, header=CSRF_HEADER),
    )

    assert response.status_code == HTTPStatus.OK
    assert "access-control-allow-credentials" not in response.headers


@pytest.mark.parametrize(
    "cors_settings",
    [{"cors_allowed_origins": FRONTEND_ORIGINS, "cors_allow_private_network": True}],
)
async def test_a_preflight_with_the_private_network_flag_allows_the_private_network(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.options(
        SESSION_PATH,
        headers={
            **_preflight_headers(origin=FRONTEND_ORIGIN, header=CSRF_HEADER),
            "Access-Control-Request-Private-Network": "true",
        },
    )

    assert response.headers["access-control-allow-private-network"] == "true"


@pytest.mark.parametrize("cors_settings", [{"cors_allowed_origins": FRONTEND_ORIGINS}])
async def test_a_request_from_an_origin_outside_the_list_gets_no_cors_origin(
    cors_client: httpx.AsyncClient,
) -> None:
    response = await cors_client.get(CSRF_PATH, headers={"Origin": OTHER_ORIGIN})

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [
        ("GET", CSRF_PATH, HTTPStatus.NO_CONTENT),
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
