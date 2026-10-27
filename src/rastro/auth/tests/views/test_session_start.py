import base64
import hashlib
from datetime import UTC, datetime, timedelta
from http import HTTPStatus

import argon2
import httpx
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.auth.domain.aggregates import User
from rastro.auth.domain.value_objects import HashedPassword
from rastro.auth.infrastructure.models import SessionRow
from rastro.auth.infrastructure.repositories import SqlUserRepository
from rastro.settings import Settings

PATH = "/api/v1/auth/session/start"
CREDENTIALS = {"email": "ana@example.com", "password": "password"}


async def test_correct_credentials_start_a_session_in_a_protected_cookie(
    client: httpx.AsyncClient, user: User
) -> None:
    response = await client.post(PATH, json=CREDENTIALS)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith("rastro_session=")
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=lax" in cookie


async def test_the_database_stores_the_hash_of_the_token_and_never_the_token(
    client: httpx.AsyncClient, user: User, db_session: AsyncSession
) -> None:
    response = await client.post(PATH, json=CREDENTIALS)

    token = response.cookies["rastro_session"]
    rows = (await db_session.execute(text("SELECT * FROM auth_session"))).all()
    assert len(rows) == 1
    assert rows[0].user_id == user.id.root
    assert rows[0].token_hash == hashlib.sha256(token.encode()).digest()
    assert token not in "".join(str(value) for value in rows[0])
    assert len(base64.urlsafe_b64decode(f"{token}=")) == 32


async def test_a_session_ends_a_fixed_time_after_it_starts(
    client: httpx.AsyncClient, user: User, db_session: AsyncSession
) -> None:
    before = datetime.now(UTC)
    response = await client.post(PATH, json=CREDENTIALS)
    after = datetime.now(UTC)

    session = await db_session.scalar(select(SessionRow))
    assert session is not None
    lifetime = timedelta(days=14)
    assert before + lifetime <= session.expires_at <= after + lifetime
    assert "Max-Age=1209600" in response.headers["Set-Cookie"]


async def test_the_session_cookie_takes_its_name_lifetime_and_flags_from_the_settings(
    client: httpx.AsyncClient, user: User, other_session_cookie: Settings
) -> None:
    response = await client.post(PATH, json=CREDENTIALS)

    assert response.status_code == HTTPStatus.NO_CONTENT
    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith("other_session=")
    assert "Max-Age=3600" in cookie
    assert "HttpOnly" not in cookie
    assert "Secure" not in cookie
    assert "SameSite=strict" in cookie


async def test_an_unknown_email_and_a_wrong_password_answer_the_same_problem(
    client: httpx.AsyncClient, user: User
) -> None:
    wrong_password = await client.post(
        PATH, json={**CREDENTIALS, "password": "wrongpassword"}
    )
    unknown_email = await client.post(
        PATH, json={**CREDENTIALS, "email": "nobody@example.com"}
    )

    for response in (wrong_password, unknown_email):
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.headers["Content-Type"] == "application/problem+json"
        assert response.json() == {"type": "auth.incorrect_credentials", "status": 401}
        assert "Set-Cookie" not in response.headers


async def test_a_correct_sign_in_replaces_a_hash_with_outdated_parameters(
    client: httpx.AsyncClient,
    user: User,
    db_session: AsyncSession,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    outdated = argon2.PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
    user.hashed_password = HashedPassword(outdated.hash("password"))
    await SqlUserRepository(db_session).update(user)
    await db_session.commit()

    response = await client.post(PATH, json=CREDENTIALS)

    async with sessionmaker() as reader:
        rehashed = await SqlUserRepository(reader).get_by_id(user.id)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert rehashed is not None
    assert rehashed.hashed_password.root.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert argon2.PasswordHasher().verify(rehashed.hashed_password.root, "password")


async def test_a_second_sign_in_starts_a_second_session(
    client: httpx.AsyncClient, user: User, db_session: AsyncSession
) -> None:
    first = await client.post(PATH, json=CREDENTIALS)
    second = await client.post(PATH, json=CREDENTIALS)

    assert first.status_code == second.status_code == HTTPStatus.NO_CONTENT
    assert first.cookies["rastro_session"] != second.cookies["rastro_session"]
    count = await db_session.scalar(select(func.count()).select_from(SessionRow))
    assert count == 2


async def test_a_sign_in_without_the_csrf_token_starts_no_session(
    client: httpx.AsyncClient, user: User
) -> None:
    del client.headers["X-CSRF-Token"]

    response = await client.post(PATH, json=CREDENTIALS)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"type": "request.csrf_failed", "status": 403}
    assert "Set-Cookie" not in response.headers
