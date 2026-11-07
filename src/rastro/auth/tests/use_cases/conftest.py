from datetime import timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    ResetToken,
    ResetTokenCooldown,
    ResetTokenLifetime,
    SessionLifetime,
    SessionToken,
)
from rastro.auth.tests.fakes import (
    FakeClock,
    FakePasswordResetJobs,
    FakeResetTokenRepository,
    FakeSessionRepository,
    FakeUserRepository,
)

LIFETIME = SessionLifetime(timedelta(seconds=1))
RESET_TOKEN_LIFETIME = ResetTokenLifetime(timedelta(hours=1))
RESET_TOKEN_COOLDOWN = ResetTokenCooldown(timedelta(seconds=60))


@pytest.fixture
def users() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def sessions() -> FakeSessionRepository:
    return FakeSessionRepository()


@pytest.fixture
def reset_tokens() -> FakeResetTokenRepository:
    return FakeResetTokenRepository()


@pytest.fixture
def password_reset_jobs() -> FakePasswordResetJobs:
    return FakePasswordResetJobs()


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


@pytest.fixture
async def reset_token(
    ana: User, reset_tokens: FakeResetTokenRepository, clock: FakeClock
) -> ResetToken:
    """The token of a Reset token of `ana` in `reset_tokens`, issued at `clock.now()`."""
    token = ResetToken(SecretStr("reset"))
    await reset_tokens.replace_after_cooldown(
        IssuedResetToken.issue(
            id=await reset_tokens.next_id(),
            user_id=ana.id,
            token=token,
            at=clock.now(),
            lifetime=RESET_TOKEN_LIFETIME,
        ),
        cooldown=RESET_TOKEN_COOLDOWN,
    )
    return token


@pytest.fixture
async def expired_reset_token(
    users: FakeUserRepository, reset_tokens: FakeResetTokenRepository, clock: FakeClock
) -> IssuedResetToken:
    """A Reset token of a second User in `reset_tokens` that runs out at `clock.now()`."""
    bia = User(
        id=await users.next_id(),
        email=Email("bia@x.com"),
        display_name=DisplayName("Bia"),
        hashed_password=HashedPassword("fake$password"),
    )
    await users.add(bia)
    expired = IssuedResetToken.issue(
        id=await reset_tokens.next_id(),
        user_id=bia.id,
        token=ResetToken(SecretStr("expired")),
        at=clock.now() - RESET_TOKEN_LIFETIME.root,
        lifetime=RESET_TOKEN_LIFETIME,
    )
    await reset_tokens.replace_after_cooldown(expired, cooldown=RESET_TOKEN_COOLDOWN)
    return expired
