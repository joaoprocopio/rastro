from http import HTTPStatus

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import User
from rastro.auth.infrastructure.models import UserRow
from rastro.settings import Settings

PATH = "/api/v1/auth/register"
VALID_BODY = {
    "email": "ada@example.com",
    "display_name": "Ada",
    "password": "supersecret",
}


async def _user_count(db_session: AsyncSession) -> int:
    count = await db_session.scalar(select(func.count()).select_from(UserRow))
    assert count is not None
    return count


async def test_a_valid_body_registers_the_user_with_no_body(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(PATH, json=VALID_BODY)

    assert response.status_code == HTTPStatus.CREATED
    assert response.content == b""


async def test_the_user_holds_the_normalized_email_and_an_argon2_hash(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    await client.post(
        PATH, json={**VALID_BODY, "email": " Ada@Example.COM ", "display_name": " Ada "}
    )

    user = await db_session.scalar(select(UserRow))
    assert user is not None
    assert user.email == "ada@example.com"
    assert user.display_name == "Ada"
    assert user.hashed_password.startswith("$argon2id$")
    assert "supersecret" not in user.hashed_password


async def test_an_email_in_use_is_a_conflict(
    client: httpx.AsyncClient, user: User, db_session: AsyncSession
) -> None:
    response = await client.post(PATH, json={**VALID_BODY, "email": " ANA@example.com"})

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "auth.email_in_use", "status": 409}
    count = await db_session.scalar(
        select(func.count()).where(UserRow.email == user.email.root)
    )
    assert count == 1


async def test_each_invalid_field_names_the_rule_that_failed(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.post(
        PATH, json={"email": "nope", "display_name": "Ada", "password": "short"}
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/email", "type": "request.invalid_format"},
            {"pointer": "#/password", "type": "request.too_short", "min_length": 8},
        ],
    }
    assert await _user_count(db_session) == 0


async def test_an_email_longer_than_254_characters_is_too_long(
    client: httpx.AsyncClient,
) -> None:
    local_part = "a" * (255 - len("@example.com"))

    response = await client.post(
        PATH, json={**VALID_BODY, "email": f"{local_part}@example.com"}
    )

    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/email", "type": "request.too_long", "max_length": 254}
        ],
    }


async def test_a_display_name_longer_than_320_characters_is_too_long(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(PATH, json={**VALID_BODY, "display_name": "x" * 321})

    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/display_name", "type": "request.too_long", "max_length": 320}
        ],
    }


async def test_a_missing_field_a_wrong_type_and_an_unknown_field_keep_their_types(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        PATH, json={"email": 1, "password": "supersecret", "role": "admin"}
    )

    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/email", "type": "request.invalid_type"},
            {"pointer": "#/display_name", "type": "request.field_required"},
            {"pointer": "#/role", "type": "request.unknown_field"},
        ],
    }


async def test_a_get_is_a_problem_405(client: httpx.AsyncClient) -> None:
    response = await client.get(PATH)

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response.headers["Allow"] == "POST"
    assert response.json() == {"type": "request.method_not_allowed", "status": 405}


async def test_a_registration_without_the_csrf_token_registers_no_user(
    client: httpx.AsyncClient, db_session: AsyncSession, settings: Settings
) -> None:
    del client.headers[settings.csrf_header_name]

    response = await client.post(PATH, json=VALID_BODY)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"type": "request.csrf_failed", "status": 403}
    assert await _user_count(db_session) == 0
