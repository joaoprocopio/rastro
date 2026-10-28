from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import SessionLifetime, SessionToken
from rastro.auth.infrastructure.repositories import SqlSessionRepository

START = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
TOKEN = SessionToken(SecretStr("token"))


@pytest.fixture
def sessions(db_session: AsyncSession) -> SqlSessionRepository:
    return SqlSessionRepository(db_session)


@pytest.fixture
async def session(sessions: SqlSessionRepository, user: User) -> Session:
    """A Session of `user` for `TOKEN`, which the test has not added yet."""
    return Session.start(
        id=await sessions.next_id(),
        user_id=user.id,
        token=TOKEN,
        at=START,
        lifetime=SessionLifetime(timedelta(days=14)),
    )


async def test_get_by_hashed_token_reads_back_every_field_that_add_wrote(
    sessions: SqlSessionRepository,
    session: Session,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await sessions.add(session)

    # A second session reads the row from the database, not from the first's cache.
    async with sessionmaker() as reader:
        assert (
            await SqlSessionRepository(reader).get_by_hashed_token(TOKEN.digest())
            == session
        )


async def test_get_by_hashed_token_answers_none_for_an_unknown_session(
    sessions: SqlSessionRepository,
) -> None:
    assert await sessions.get_by_hashed_token(TOKEN.digest()) is None


async def test_two_next_id_calls_return_two_different_ids(
    sessions: SqlSessionRepository,
) -> None:
    assert await sessions.next_id() != await sessions.next_id()


async def test_remove_deletes_the_session(
    sessions: SqlSessionRepository,
    session: Session,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await sessions.add(session)

    await sessions.remove(session)

    async with sessionmaker() as reader:
        assert (
            await SqlSessionRepository(reader).get_by_hashed_token(TOKEN.digest())
            is None
        )
