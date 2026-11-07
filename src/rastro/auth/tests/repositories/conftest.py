import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.ports import (
    ResetTokenRepository,
    SessionRepository,
    UserRepository,
)
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    ResetToken,
    ResetTokenLifetime,
    SessionLifetime,
    SessionToken,
)
from rastro.auth.infrastructure.repositories import (
    SqlResetTokenRepository,
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.auth.tests.fakes import (
    FakeResetTokenRepository,
    FakeSessionRepository,
    FakeUserRepository,
)
from rastro.common.infrastructure.database import create_sessionmaker
from rastro.common.tests.adapter import RepositoryKind

START = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
LIFETIME = SessionLifetime(timedelta(days=14))
RESET_TOKEN_LIFETIME = ResetTokenLifetime(timedelta(hours=1))
COMMITTED_TOKEN = ResetToken(SecretStr("committed"))
STATEMENTS_THAT_WAIT = text(
    "SELECT count(*) FROM pg_stat_activity"
    " WHERE datname = current_database()"
    " AND wait_event_type = 'Lock' AND query LIKE :statement"
)


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
def reset_tokens(
    adapter: RepositoryKind, request: pytest.FixtureRequest
) -> ResetTokenRepository:
    return adapter.pick(
        fake=FakeResetTokenRepository,
        sql=lambda: SqlResetTokenRepository(request.getfixturevalue("db_session")),
    )


@pytest.fixture
def read_reset_tokens(
    adapter: RepositoryKind,
    reset_tokens: ResetTokenRepository,
    request: pytest.FixtureRequest,
) -> ResetTokenRepository:
    """The repository that reads back what `reset_tokens` wrote."""
    return adapter.pick(
        fake=lambda: reset_tokens,
        sql=lambda: SqlResetTokenRepository(request.getfixturevalue("reader")),
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


@pytest.fixture
async def bia(users: UserRepository) -> User:
    """A second User of `users`, which the test has not added yet."""
    return User(
        id=await users.next_id(),
        email=Email("bia@x.com"),
        display_name=DisplayName("Bia"),
        hashed_password=HashedPassword("fake$password"),
    )


@pytest.fixture
async def issued_reset_token(
    reset_tokens: ResetTokenRepository, users: UserRepository, ana: User
) -> IssuedResetToken:
    """A Reset token of the added `ana`, which the test has not stored yet."""
    await users.add(ana)
    return IssuedResetToken.issue(
        id=await reset_tokens.next_id(),
        user_id=ana.id,
        token=ResetToken(SecretStr("token")),
        at=START,
        lifetime=RESET_TOKEN_LIFETIME,
    )


@pytest.fixture
async def newer_reset_token(
    reset_tokens: ResetTokenRepository, issued_reset_token: IssuedResetToken, ana: User
) -> IssuedResetToken:
    """A Reset token of `ana` issued one hour after `issued_reset_token`, not stored yet."""
    return IssuedResetToken.issue(
        id=await reset_tokens.next_id(),
        user_id=ana.id,
        token=ResetToken(SecretStr("newer")),
        at=START + timedelta(hours=1),
        lifetime=RESET_TOKEN_LIFETIME,
    )


@pytest.fixture
async def committed_user(engine: AsyncEngine) -> AsyncIterator[User]:
    """A User that every connection sees, which the test does not roll back."""
    sessionmaker = create_sessionmaker(engine)
    async with sessionmaker.begin() as db_session:
        users = SqlUserRepository(db_session)
        user = User(
            id=await users.next_id(),
            email=Email("committed@x.com"),
            display_name=DisplayName("Committed"),
            hashed_password=HashedPassword("fake$password"),
        )
        await users.add(user)

    yield user

    # The foreign key deletes each Session and the Reset token with their User.
    async with sessionmaker.begin() as db_session:
        await db_session.execute(
            text("DELETE FROM auth_user WHERE id = :id"), {"id": user.id.root}
        )


@pytest.fixture
async def committed_reset_token(
    engine: AsyncEngine, committed_user: User
) -> IssuedResetToken:
    """A Reset token of `committed_user` that every connection sees."""
    async with create_sessionmaker(engine).begin() as db_session:
        reset_tokens = SqlResetTokenRepository(db_session)
        issued_reset_token = IssuedResetToken.issue(
            id=await reset_tokens.next_id(),
            user_id=committed_user.id,
            token=COMMITTED_TOKEN,
            at=START,
            lifetime=RESET_TOKEN_LIFETIME,
        )
        await reset_tokens.replace(issued_reset_token)
    return issued_reset_token


@pytest.fixture
async def raced_user(
    engine: AsyncEngine,
    committed_user: User,
    committed_reset_token: IssuedResetToken,
    request: pytest.FixtureRequest,
) -> User:
    """`committed_user`, with `COMMITTED_TOKEN` and each kind of hash of `password`."""
    committed_user.hashed_password = HashedPassword(request.param)
    async with create_sessionmaker(engine).begin() as db_session:
        await SqlUserRepository(db_session).update(committed_user)
    return committed_user


@pytest.fixture
async def until_a_statement_waits(
    engine: AsyncEngine,
) -> AsyncIterator[Callable[[str], Awaitable[None]]]:
    """Return once a statement that matches the `LIKE` pattern waits for a lock."""
    async with create_sessionmaker(engine)() as probe:

        async def until(statement: str) -> None:
            async with asyncio.timeout(5):
                while not await probe.scalar(
                    STATEMENTS_THAT_WAIT, {"statement": statement}
                ):
                    # A transaction reads pg_stat_activity once, so each read needs a new one.
                    await probe.rollback()

        yield until
