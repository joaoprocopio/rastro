import base64
from http import HTTPStatus

import httpx
import pytest
from fastapi import FastAPI

from rastro.common.presentation.dependencies import app_settings
from rastro.settings import SameSite, Settings

PATH = "/api/v1/security/csrf"
# The sample router runs the CSRF check on this command.
SAMPLE_COMMAND = "/sample/csrf"


async def test_the_csrf_cookie_is_readable_by_scripts(
    sample_client: httpx.AsyncClient, settings: Settings
) -> None:
    response = await sample_client.get(PATH)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith(f"{settings.csrf_cookie_name}=")
    assert "HttpOnly" not in cookie
    assert "Secure" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/" in cookie
    token = response.cookies[settings.csrf_cookie_name]
    assert len(base64.urlsafe_b64decode(f"{token}=")) == 32


async def test_each_request_sets_a_new_token(
    sample_client: httpx.AsyncClient, settings: Settings
) -> None:
    first = await sample_client.get(PATH)
    second = await sample_client.get(PATH)

    assert (
        first.cookies[settings.csrf_cookie_name]
        != second.cookies[settings.csrf_cookie_name]
    )


@pytest.mark.parametrize("old_path", ["/api/v1/auth/csrf", "/api/v1/csrf"])
async def test_an_old_route_is_not_found(
    sample_client: httpx.AsyncClient, old_path: str
) -> None:
    response = await sample_client.get(old_path)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"type": "request.not_found", "status": 404}


async def test_the_token_of_the_cookie_lets_a_post_through(
    sample_client: httpx.AsyncClient, settings: Settings
) -> None:
    sample_client.cookies.clear()
    del sample_client.headers[settings.csrf_header_name]
    token = (await sample_client.get(PATH)).cookies[settings.csrf_cookie_name]

    response = await sample_client.post(
        SAMPLE_COMMAND, headers={settings.csrf_header_name: token}
    )

    assert response.status_code == HTTPStatus.NO_CONTENT


async def test_the_token_of_the_cookie_without_the_header_fails(
    sample_client: httpx.AsyncClient, settings: Settings
) -> None:
    sample_client.cookies.clear()
    del sample_client.headers[settings.csrf_header_name]
    await sample_client.get(PATH)

    response = await sample_client.post(SAMPLE_COMMAND)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"type": "security.csrf_failed", "status": 403}


async def test_the_settings_choose_the_csrf_cookie_and_header(
    sample_app: FastAPI, sample_client: httpx.AsyncClient, settings: Settings
) -> None:
    sample_app.dependency_overrides[app_settings] = lambda: settings.model_copy(
        update={
            "csrf_cookie_name": "other_csrf",
            "csrf_header_name": "X-Other-CSRF",
            "csrf_cookie_secure": False,
            "csrf_cookie_httponly": True,
            "csrf_cookie_samesite": SameSite.STRICT,
        }
    )
    sample_client.cookies.clear()
    sample_client.headers.clear()

    response = await sample_client.get(PATH)
    token = response.cookies["other_csrf"]
    after = await sample_client.post(SAMPLE_COMMAND, headers={"X-Other-CSRF": token})

    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith("other_csrf=")
    assert "Secure" not in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert after.status_code == HTTPStatus.NO_CONTENT
