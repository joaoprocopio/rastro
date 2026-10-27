from datetime import UTC, datetime

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import SessionToken
from rastro.auth.infrastructure.repositories import SqlSessionRepository

START = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
TOKEN = SessionToken("token")


@pytest.fixture
def sessions(db_session: AsyncSession) -> SqlSessionRepository:
    return SqlSessionRepository(db_session)


@pytest.fixture
async def session(sessions: SqlSessionRepository, user: User) -> Session:
    """A Session of `user` for `TOKEN`, which the test has not added yet."""
    return Session.start(
        id=await sessions.next_id(), user_id=user.id, token=TOKEN, at=START
    )


async def test_get_by_id_and_get_by_token_hash_read_back_every_field_that_add_wrote(
    sessions: SqlSessionRepository,
    session: Session,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await sessions.add(session)

    # A second session reads the row from the database, not from the first's cache.
    async with sessionmaker() as reader:
        assert await SqlSessionRepository(reader).get_by_id(session.id) == session
        assert (
            await SqlSessionRepository(reader).get_by_token_hash(TOKEN.digest())
            == session
        )


async def test_get_by_id_and_get_by_token_hash_answer_none_for_an_unknown_session(
    sessions: SqlSessionRepository,
) -> None:
    assert await sessions.get_by_id(1) is None
    assert await sessions.get_by_token_hash(TOKEN.digest()) is None


async def test_two_next_id_calls_return_two_different_ids(
    sessions: SqlSessionRepository,
) -> None:
    assert await sessions.next_id() != await sessions.next_id()


async def test_update_writes_every_field_of_the_session(
    sessions: SqlSessionRepository,
    session: Session,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await sessions.add(session)
    session.token_hash = SessionToken("other").digest()
    session.expires_at = datetime(2026, 2, 1, tzinfo=UTC)

    await sessions.update(session)

    async with sessionmaker() as reader:
        assert await SqlSessionRepository(reader).get_by_id(session.id) == session


async def test_update_of_a_session_with_no_row_raises_lookup_error_and_adds_no_row(
    sessions: SqlSessionRepository,
    session: Session,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    with pytest.raises(LookupError):
        await sessions.update(session)

    async with sessionmaker() as reader:
        assert await SqlSessionRepository(reader).get_by_id(session.id) is None


async def test_remove_deletes_the_session(
    sessions: SqlSessionRepository,
    session: Session,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await sessions.add(session)

    await sessions.remove(session)

    async with sessionmaker() as reader:
        assert await SqlSessionRepository(reader).get_by_id(session.id) is None


async def test_add_read_and_remove_set_the_user_id_on_the_current_span(
    sessions: SqlSessionRepository,
    session: Session,
    user: User,
    spans: InMemorySpanExporter,
) -> None:
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("add"):
        await sessions.add(session)
    with tracer.start_as_current_span("read"):
        await sessions.get_by_token_hash(TOKEN.digest())
    with tracer.start_as_current_span("remove"):
        await sessions.remove(session)

    user_ids = {
        span.name: (span.attributes or {}).get("user.id")
        for span in spans.get_finished_spans()
        if span.name in {"add", "read", "remove"}
    }
    assert user_ids == {"add": user.id, "read": user.id, "remove": user.id}
