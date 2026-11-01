from datetime import timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    SessionLifetime,
    SessionToken,
)
from rastro.auth.tests.fakes import FakeClock, FakeSessionRepository, FakeUserRepository

LIFETIME = SessionLifetime(timedelta(seconds=1))


@pytest.fixture
def users() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def sessions() -> FakeSessionRepository:
    return FakeSessionRepository()


@pytest.fixture
async def ana(users: FakeUserRepository) -> User:
    """Ana, `ana@x.com`, whose password `password` has a current hash."""
    ana = User(
        id=await users.next_id(),
        email=Email("ana@x.com"),
        display_name=DisplayName("Ana"),
        hashed_password=HashedPassword("fake$password"),
    )
    await users.add(ana)
    return ana


@pytest.fixture
async def session_token(
    ana: User, sessions: FakeSessionRepository, clock: FakeClock
) -> SessionToken:
    """The token of a Session of `ana` in `sessions`, one second from expiry."""
    token = SessionToken(SecretStr("mine"))
    await sessions.add(
        Session(
            id=await sessions.next_id(),
            user_id=ana.id,
            hashed_token=token.digest(),
            expires_at=clock.now() + timedelta(seconds=1),
        )
    )
    return token


@pytest.fixture
async def active_session(
    ana: User, sessions: FakeSessionRepository, clock: FakeClock
) -> Session:
    """A Session of `ana` in `sessions` that expires one second after `clock.now()`."""
    session = Session.start(
        id=await sessions.next_id(),
        user_id=ana.id,
        token=SessionToken(SecretStr("active")),
        at=clock.now(),
        lifetime=LIFETIME,
    )
    await sessions.add(session)
    return session


@pytest.fixture
async def expired_session(
    ana: User, sessions: FakeSessionRepository, clock: FakeClock
) -> Session:
    """A Session of `ana` in `sessions` whose lifetime runs out at `clock.now()`."""
    session = Session.start(
        id=await sessions.next_id(),
        user_id=ana.id,
        token=SessionToken(SecretStr("expired")),
        at=clock.now() - LIFETIME.root,
        lifetime=LIFETIME,
    )
    await sessions.add(session)
    return session
