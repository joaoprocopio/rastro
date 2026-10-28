from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.ports import SessionRepository, UserRepository
from rastro.auth.domain.value_objects import SessionLifetime, SessionToken

START = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
LIFETIME = SessionLifetime(timedelta(days=14))
TOKEN = SessionToken(SecretStr("token"))
OTHER_TOKEN = SessionToken(SecretStr("other"))


@pytest.fixture
async def session(
    sessions: SessionRepository, users: UserRepository, ana: User
) -> Session:
    """A Session of the added `ana` for `TOKEN`, which the test has not added yet."""
    await users.add(ana)
    return Session.start(
        id=await sessions.next_id(),
        user_id=ana.id,
        token=TOKEN,
        at=START,
        lifetime=LIFETIME,
    )


async def test_get_by_hashed_token_reads_back_every_field_that_add_wrote(
    sessions: SessionRepository, read_sessions: SessionRepository, session: Session
) -> None:
    await sessions.add(session)

    assert await read_sessions.get_by_hashed_token(TOKEN.digest()) == session


async def test_get_by_hashed_token_answers_none_for_an_unknown_session(
    sessions: SessionRepository,
) -> None:
    assert await sessions.get_by_hashed_token(TOKEN.digest()) is None


async def test_two_next_id_calls_return_two_different_ids(
    sessions: SessionRepository,
) -> None:
    assert await sessions.next_id() != await sessions.next_id()


async def test_remove_deletes_the_session(
    sessions: SessionRepository, read_sessions: SessionRepository, session: Session
) -> None:
    await sessions.add(session)

    await sessions.remove(session)

    assert await read_sessions.get_by_hashed_token(TOKEN.digest()) is None


async def test_remove_of_a_missing_session_raises_lookup_error_and_keeps_the_others(
    sessions: SessionRepository,
    read_sessions: SessionRepository,
    session: Session,
    ana: User,
) -> None:
    await sessions.add(session)
    missing = Session.start(
        id=await sessions.next_id(),
        user_id=ana.id,
        token=OTHER_TOKEN,
        at=START,
        lifetime=LIFETIME,
    )

    with pytest.raises(LookupError, match=f"with the id {missing.id.root}\\."):
        await sessions.remove(missing)

    assert await read_sessions.get_by_hashed_token(TOKEN.digest()) == session


async def test_a_field_assigned_with_no_update_keeps_its_stored_value(
    sessions: SessionRepository, read_sessions: SessionRepository, session: Session
) -> None:
    await sessions.add(session)
    session.expires_at = START
    read = await read_sessions.get_by_hashed_token(TOKEN.digest())
    if read is not None:
        read.expires_at = START

    stored = await read_sessions.get_by_hashed_token(TOKEN.digest())

    assert read is not None
    assert stored is not None
    assert stored.expires_at == START + LIFETIME.root
