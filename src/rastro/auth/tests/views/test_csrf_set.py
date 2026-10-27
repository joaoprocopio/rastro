import base64
from http import HTTPStatus

import httpx

from rastro.common.presentation.views import CSRF_COOKIE, CSRF_HEADER

PATH = "/api/v1/auth/csrf"


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
