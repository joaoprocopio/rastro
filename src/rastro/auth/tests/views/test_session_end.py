from datetime import UTC, datetime
from http import HTTPStatus

import httpx
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import User
from rastro.auth.infrastructure.models import SessionRow
from rastro.settings import Settings

PATH = "/api/v1/auth/session/end"
NOT_AUTHENTICATED = {"type": "auth.not_authenticated", "status": 401}


async def test_ending_a_session_deletes_it_and_clears_the_cookie(
    signed_in_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    response = await signed_in_client.post(PATH)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith('rastro_session="";')
    assert "Max-Age=0" in cookie
    count = await db_session.scalar(select(func.count()).select_from(SessionRow))
    assert count == 0


async def test_ending_a_session_clears_the_cookie_named_in_the_settings(
    signed_in_client: httpx.AsyncClient, other_session_cookie_settings: Settings
) -> None:
    token = signed_in_client.cookies["rastro_session"]
    signed_in_client.cookies.delete("rastro_session")
    signed_in_client.cookies.set("other_session", token)

    response = await signed_in_client.post(PATH)

    assert response.status_code == HTTPStatus.NO_CONTENT
    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith('other_session="";')
    assert "Max-Age=0" in cookie
    assert "Secure" not in cookie
    assert "SameSite=strict" in cookie


async def test_ending_without_a_session_token_is_not_authenticated(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(PATH)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json() == NOT_AUTHENTICATED


async def test_ending_with_a_token_that_no_session_holds_is_not_authenticated(
    client: httpx.AsyncClient, user: User
) -> None:
    client.cookies.set("rastro_session", "unknown")

    response = await client.post(PATH)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == NOT_AUTHENTICATED


async def test_ending_a_session_past_its_expiry_is_not_authenticated(
    signed_in_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await db_session.execute(
        text("UPDATE auth_session SET expires_at = :now"), {"now": datetime.now(UTC)}
    )
    await db_session.commit()

    response = await signed_in_client.post(PATH)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == NOT_AUTHENTICATED
    count = await db_session.scalar(select(func.count()).select_from(SessionRow))
    assert count == 1
