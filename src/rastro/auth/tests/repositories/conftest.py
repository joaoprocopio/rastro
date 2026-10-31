from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.ports import SessionRepository, UserRepository
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    SessionLifetime,
    SessionToken,
)
from rastro.auth.infrastructure.repositories import (
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.auth.tests.fakes import FakeSessionRepository, FakeUserRepository
from rastro.common.tests.adapter import RepositoryKind

START = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
LIFETIME = SessionLifetime(timedelta(days=14))


@pytest.fixture
def users(adapter: RepositoryKind, request: pytest.FixtureRequest) -> UserRepository:
    return adapter.pick(
        fake=FakeUserRepository,
        sql=lambda: SqlUserRepository(request.getfixturevalue("db_session")),
    )


@pytest.fixture
def read_users(
    adapter: RepositoryKind, users: UserRepository, request: pytest.FixtureRequest
) -> UserRepository:
    """The repository that reads back what `users` wrote."""
    return adapter.pick(
        fake=lambda: users,
        sql=lambda: SqlUserRepository(request.getfixturevalue("reader")),
    )


@pytest.fixture
def sessions(
    adapter: RepositoryKind, request: pytest.FixtureRequest
) -> SessionRepository:
    return adapter.pick(
        fake=FakeSessionRepository,
        sql=lambda: SqlSessionRepository(request.getfixturevalue("db_session")),
    )


@pytest.fixture
def read_sessions(
    adapter: RepositoryKind, sessions: SessionRepository, request: pytest.FixtureRequest
) -> SessionRepository:
    """The repository that reads back what `sessions` wrote."""
    return adapter.pick(
        fake=lambda: sessions,
        sql=lambda: SqlSessionRepository(request.getfixturevalue("reader")),
    )


@pytest.fixture
async def ana(users: UserRepository) -> User:
    """A User with the next id of `users`, which the test has not added yet."""
    return User(
        id=await users.next_id(),
        email=Email("ana@x.com"),
        display_name=DisplayName("Ana"),
        hashed_password=HashedPassword("fake$password"),
    )


@pytest.fixture
async def session(
    sessions: SessionRepository, users: UserRepository, ana: User
) -> Session:
    """A Session of the added `ana`, which the test has not added yet."""
    await users.add(ana)
    return Session.start(
        id=await sessions.next_id(),
        user_id=ana.id,
        token=SessionToken(SecretStr("token")),
        at=START,
        lifetime=LIFETIME,
    )


@pytest.fixture
async def earlier_session(
    sessions: SessionRepository, session: Session, ana: User
) -> Session:
    """A Session of `ana` that expires one day before `session`, not added yet."""
    return Session.start(
        id=await sessions.next_id(),
        user_id=ana.id,
        token=SessionToken(SecretStr("other")),
        at=START - timedelta(days=1),
        lifetime=LIFETIME,
    )
