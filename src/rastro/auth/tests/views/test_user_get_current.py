from datetime import UTC, datetime
from http import HTTPStatus

import httpx
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import User

PATH = "/api/v1/auth/session"
NOT_AUTHENTICATED = {"type": "auth.not_authenticated", "status": 401}


async def test_a_session_answers_the_email_and_display_name_of_its_user(
    signed_in_client: httpx.AsyncClient,
) -> None:
    response = await signed_in_client.get(PATH)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == {"email": "ana@example.com", "display_name": "Ana"}


async def test_no_session_is_not_authenticated(client: httpx.AsyncClient) -> None:
    response = await client.get(PATH)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json() == NOT_AUTHENTICATED


async def test_a_token_that_no_session_holds_is_not_authenticated(
    client: httpx.AsyncClient, user: User
) -> None:
    client.cookies.set("rastro_session", "not a token; at all")

    response = await client.get(PATH)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == NOT_AUTHENTICATED


async def test_an_ended_session_is_not_authenticated(
    signed_in_client: httpx.AsyncClient,
) -> None:
    token = signed_in_client.cookies["rastro_session"]
    await signed_in_client.post("/api/v1/auth/session/end")
    signed_in_client.cookies.set("rastro_session", token)

    response = await signed_in_client.get(PATH)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == NOT_AUTHENTICATED


async def test_a_session_past_its_expiry_is_not_authenticated(
    signed_in_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await db_session.execute(
        text("UPDATE auth_session SET expires_at = :now"), {"now": datetime.now(UTC)}
    )
    await db_session.commit()

    response = await signed_in_client.get(PATH)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == NOT_AUTHENTICATED


async def test_a_user_whose_email_fails_its_value_object_is_an_internal_error(
    app: FastAPI, signed_in_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await db_session.execute(text("UPDATE auth_user SET email = 'not-an-email'"))
    await db_session.commit()
    # The 500 handler sends its response and then raises the exception again.
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://testserver",
        cookies=signed_in_client.cookies,
    ) as client:
        response = await client.get(PATH)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "server.internal_error", "status": 500}
