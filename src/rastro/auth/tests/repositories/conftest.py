import pytest

from rastro.auth.domain.ports import SessionRepository, UserRepository
from rastro.auth.infrastructure.repositories import (
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.auth.tests.fakes import FakeSessionRepository, FakeUserRepository


@pytest.fixture
def users(adapter: str, request: pytest.FixtureRequest) -> UserRepository:
    if adapter == "fake":
        return FakeUserRepository()
    return SqlUserRepository(request.getfixturevalue("db_session"))


@pytest.fixture
def read_users(
    adapter: str, users: UserRepository, request: pytest.FixtureRequest
) -> UserRepository:
    """The repository that reads back what `users` wrote."""
    if adapter == "fake":
        return users
    return SqlUserRepository(request.getfixturevalue("reader"))


@pytest.fixture
def sessions(adapter: str, request: pytest.FixtureRequest) -> SessionRepository:
    if adapter == "fake":
        return FakeSessionRepository()
    return SqlSessionRepository(request.getfixturevalue("db_session"))


@pytest.fixture
def read_sessions(
    adapter: str, sessions: SessionRepository, request: pytest.FixtureRequest
) -> SessionRepository:
    """The repository that reads back what `sessions` wrote."""
    if adapter == "fake":
        return sessions
    return SqlSessionRepository(request.getfixturevalue("reader"))
