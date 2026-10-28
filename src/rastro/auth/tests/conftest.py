from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.ports import PasswordHasher
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    RawPassword,
    SessionToken,
)
from rastro.auth.infrastructure.repositories import (
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.settings import Settings


@pytest.fixture
async def user(db_session: AsyncSession, password_hasher: PasswordHasher) -> User:
    users = SqlUserRepository(db_session)
    user = User(
        id=await users.next_id(),
        email=Email("ana@example.com"),
        display_name=DisplayName("Ana"),
        hashed_password=password_hasher.hash(
            password=RawPassword(SecretStr("password"))
        ),
    )
    await users.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def signed_in_client(
    app: FastAPI,
    settings: Settings,
    db_session: AsyncSession,
    user: User,
    csrf_token: str,
) -> AsyncIterator[httpx.AsyncClient]:
    # The Session goes straight into the repository, so no test pays for argon2.
    token = SessionToken.generate(nbytes=settings.session_token_bytes)
    sessions = SqlSessionRepository(db_session)
    await sessions.add(
        Session.start(
            id=await sessions.next_id(),
            user_id=user.id,
            token=token,
            at=datetime.now(UTC),
            lifetime=settings.session_lifetime,
        )
    )
    await db_session.commit()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://testserver",
        cookies={
            settings.session_cookie_name: token.root.get_secret_value(),
            settings.csrf_cookie_name: csrf_token,
        },
        headers={settings.csrf_header_name: csrf_token},
    ) as client:
        yield client
