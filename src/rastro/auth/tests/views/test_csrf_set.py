import base64
from http import HTTPStatus

import httpx
from fastapi import FastAPI

from rastro.common.presentation.dependencies import app_settings
from rastro.settings import Settings

PATH = "/api/v1/auth/csrf"
CSRF_COOKIE = "rastro_csrf"
CSRF_HEADER = "X-CSRF-Token"


async def test_the_csrf_cookie_is_readable_by_scripts(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(PATH)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith("rastro_csrf=")
    assert "HttpOnly" not in cookie
    assert "Secure" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/" in cookie
    token = response.cookies["rastro_csrf"]
    assert len(base64.urlsafe_b64decode(f"{token}=")) == 32


async def test_each_request_sets_a_new_token(client: httpx.AsyncClient) -> None:
    first = await client.get(PATH)
    second = await client.get(PATH)

    assert first.cookies["rastro_csrf"] != second.cookies["rastro_csrf"]


async def test_the_token_of_the_cookie_lets_a_post_through(
    client: httpx.AsyncClient,
) -> None:
    client.cookies.clear()
    del client.headers[CSRF_HEADER]
    token = (await client.get(PATH)).cookies[CSRF_COOKIE]

    response = await client.post(
        "/api/v1/auth/session/end", headers={CSRF_HEADER: token}
    )

    # The view answers, so the CSRF check let the request through.
    assert response.json() == {"type": "auth.not_authenticated", "status": 401}


async def test_the_settings_choose_the_csrf_cookie_and_header(
    app: FastAPI, client: httpx.AsyncClient, settings: Settings
) -> None:
    app.dependency_overrides[app_settings] = lambda: settings.model_copy(
        update={
            "csrf_cookie_name": "other_csrf",
            "csrf_header_name": "X-Other-CSRF",
            "csrf_cookie_secure": False,
            "csrf_cookie_httponly": True,
            "csrf_cookie_samesite": "strict",
        }
    )
    client.cookies.clear()
    client.headers.clear()

    response = await client.get(PATH)
    token = response.cookies["other_csrf"]
    after = await client.post(
        "/api/v1/auth/session/end", headers={"X-Other-CSRF": token}
    )

    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith("other_csrf=")
    assert "Secure" not in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    # The view answers, so the CSRF check let the request through.
    assert after.json() == {"type": "auth.not_authenticated", "status": 401}
