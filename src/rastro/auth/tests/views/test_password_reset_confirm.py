import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from http import HTTPStatus

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.ports import PasswordHasher
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    RawPassword,
    ResetToken,
)
from rastro.auth.infrastructure.models import ResetTokenRow, SessionRow
from rastro.auth.infrastructure.repositories import (
    SqlResetTokenRepository,
    SqlUserRepository,
)
from rastro.common.infrastructure.database import create_sessionmaker
from rastro.settings import Settings

PATH = "/api/v1/auth/password-reset/confirm"
SESSION_START_PATH = "/api/v1/auth/session/start"
NEW_PASSWORD = "newpassword"
INVALID_TOKEN = {"type": "auth.invalid_reset_token", "status": 400}
OLD_CREDENTIALS = {"email": "ana@example.com", "password": "password"}
NEW_CREDENTIALS = {"email": "ana@example.com", "password": NEW_PASSWORD}
RACED_TOKEN = ResetToken(SecretStr("raced"))


def _body(token: ResetToken, *, password: str = NEW_PASSWORD) -> dict[str, str]:
    return {"token": token.root.get_secret_value(), "password": password}


async def test_a_valid_token_answers_with_no_body_and_starts_no_session(
    client: httpx.AsyncClient, reset_token: ResetToken, db_session: AsyncSession
) -> None:
    response = await client.post(PATH, json=_body(reset_token))

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert "Set-Cookie" not in response.headers
    count = await db_session.scalar(select(func.count()).select_from(SessionRow))
    assert count == 0


async def test_the_new_password_starts_a_session_and_the_old_one_does_not(
    client: httpx.AsyncClient, reset_token: ResetToken
) -> None:
    await client.post(PATH, json=_body(reset_token))

    old = await client.post(SESSION_START_PATH, json=OLD_CREDENTIALS)
    new = await client.post(SESSION_START_PATH, json=NEW_CREDENTIALS)

    assert old.status_code == HTTPStatus.UNAUTHORIZED
    assert new.status_code == HTTPStatus.NO_CONTENT


async def test_a_confirmation_ends_every_session_of_the_user(
    client: httpx.AsyncClient,
    signed_in_client: httpx.AsyncClient,
    active_session: Session,
    expired_session: Session,
    reset_token: ResetToken,
    db_session: AsyncSession,
) -> None:
    before = await signed_in_client.get("/api/v1/auth/session")

    response = await client.post(PATH, json=_body(reset_token))

    after = await signed_in_client.get("/api/v1/auth/session")
    assert before.status_code == HTTPStatus.OK
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert after.status_code == HTTPStatus.UNAUTHORIZED
    count = await db_session.scalar(select(func.count()).select_from(SessionRow))
    assert count == 0


async def test_a_token_used_once_is_invalid_and_the_password_stays_the_same(
    client: httpx.AsyncClient, reset_token: ResetToken
) -> None:
    await client.post(PATH, json=_body(reset_token))

    response = await client.post(
        PATH, json=_body(reset_token, password="thirdpassword")
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json() == INVALID_TOKEN
    third = await client.post(
        SESSION_START_PATH,
        json={"email": "ana@example.com", "password": "thirdpassword"},
    )
    new = await client.post(SESSION_START_PATH, json=NEW_CREDENTIALS)
    assert third.status_code == HTTPStatus.UNAUTHORIZED
    assert new.status_code == HTTPStatus.NO_CONTENT


async def test_an_expired_token_is_invalid_and_changes_nothing(
    client: httpx.AsyncClient, expired_reset_token: ResetToken
) -> None:
    response = await client.post(PATH, json=_body(expired_reset_token))

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == INVALID_TOKEN
    old = await client.post(SESSION_START_PATH, json=OLD_CREDENTIALS)
    assert old.status_code == HTTPStatus.NO_CONTENT


async def test_an_expired_token_keeps_its_row_for_the_hourly_task(
    client: httpx.AsyncClient,
    expired_reset_token: ResetToken,
    db_session: AsyncSession,
) -> None:
    await client.post(PATH, json=_body(expired_reset_token))

    count = await db_session.scalar(select(func.count()).select_from(ResetTokenRow))
    assert count == 1


@pytest.mark.parametrize("token", ["unknown", "", "n\u00e3o"])
async def test_an_unknown_token_is_the_same_invalid_token_problem(
    client: httpx.AsyncClient, user: User, token: str
) -> None:
    response = await client.post(PATH, json={"token": token, "password": NEW_PASSWORD})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == INVALID_TOKEN


async def test_a_token_with_a_lone_surrogate_is_the_same_invalid_token_problem(
    client: httpx.AsyncClient, user: User
) -> None:
    # The JSON encoder of httpx rejects a lone surrogate, so the body stays literal.
    response = await client.post(
        PATH,
        content='{"token": "\\ud800", "password": "newpassword"}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == INVALID_TOKEN


async def test_a_password_that_raw_password_rejects_keeps_the_token_working(
    client: httpx.AsyncClient, reset_token: ResetToken
) -> None:
    rejected = await client.post(PATH, json=_body(reset_token, password="short"))

    assert rejected.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert rejected.headers["Content-Type"] == "application/problem+json"
    assert rejected.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/password", "type": "request.too_short", "min_length": 8}
        ],
    }
    accepted = await client.post(PATH, json=_body(reset_token))
    assert accepted.status_code == HTTPStatus.NO_CONTENT


async def test_a_new_password_with_a_lone_surrogate_starts_a_session(
    client: httpx.AsyncClient, reset_token: ResetToken
) -> None:
    # The JSON encoder of httpx rejects a lone surrogate, so the body stays literal.
    confirmed = await client.post(
        PATH,
        content='{"token": "reset", "password": "\\ud800aaaaaaaa"}',
        headers={"Content-Type": "application/json"},
    )

    assert confirmed.status_code == HTTPStatus.NO_CONTENT
    started = await client.post(
        SESSION_START_PATH,
        content='{"email": "ana@example.com", "password": "\\ud800aaaaaaaa"}',
        headers={"Content-Type": "application/json"},
    )
    wrong = await client.post(
        SESSION_START_PATH,
        content='{"email": "ana@example.com", "password": "\\ud801aaaaaaaa"}',
        headers={"Content-Type": "application/json"},
    )
    assert started.status_code == HTTPStatus.NO_CONTENT
    assert wrong.status_code == HTTPStatus.UNAUTHORIZED


async def test_a_body_with_no_token_is_a_validation_problem(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(PATH, json={"password": NEW_PASSWORD})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#/token", "type": "request.field_required"}],
    }


async def test_a_confirmation_without_the_csrf_token_keeps_the_token_working(
    client: httpx.AsyncClient, reset_token: ResetToken, settings: Settings
) -> None:
    csrf_header = client.headers.pop(settings.csrf_header_name)

    rejected = await client.post(PATH, json=_body(reset_token))

    client.headers[settings.csrf_header_name] = csrf_header
    assert rejected.status_code == HTTPStatus.FORBIDDEN
    assert rejected.json() == {"type": "security.csrf_failed", "status": 403}
    accepted = await client.post(PATH, json=_body(reset_token))
    assert accepted.status_code == HTTPStatus.NO_CONTENT


@pytest.fixture
async def raced_user(
    engine: AsyncEngine, password_hasher: PasswordHasher, settings: Settings
) -> AsyncIterator[User]:
    """A User with the Reset token `RACED_TOKEN`, both committed for every connection."""
    sessionmaker = create_sessionmaker(engine)
    async with sessionmaker.begin() as db_session:
        users = SqlUserRepository(db_session)
        reset_tokens = SqlResetTokenRepository(db_session)
        user = User(
            id=await users.next_id(),
            email=Email("raced@example.com"),
            display_name=DisplayName("Raced"),
            hashed_password=password_hasher.hash(
                password=RawPassword(SecretStr("password"))
            ),
        )
        await users.add(user)
        await reset_tokens.replace_after_cooldown(
            IssuedResetToken.issue(
                id=await reset_tokens.next_id(),
                user_id=user.id,
                token=RACED_TOKEN,
                at=datetime.now(UTC),
                lifetime=settings.reset_token_lifetime,
            ),
            cooldown=settings.reset_token_cooldown,
        )

    yield user

    # The foreign key deletes the Reset token with its User.
    async with sessionmaker.begin() as db_session:
        await db_session.execute(
            text("DELETE FROM auth_user WHERE id = :id"), {"id": user.id.root}
        )


async def test_two_concurrent_confirmations_of_one_token_answer_204_and_400(
    committing_client: httpx.AsyncClient, raced_user: User
) -> None:
    first, second = await asyncio.gather(
        committing_client.post(PATH, json=_body(RACED_TOKEN, password="firstpassword")),
        committing_client.post(PATH, json=_body(RACED_TOKEN, password="otherpassword")),
    )

    responses = sorted((first, second), key=lambda response: response.status_code)
    assert [response.status_code for response in responses] == [
        HTTPStatus.NO_CONTENT,
        HTTPStatus.BAD_REQUEST,
    ]
    assert responses[1].json() == INVALID_TOKEN
