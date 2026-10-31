from datetime import timedelta

import pytest

from rastro.auth.domain.aggregates import Session
from rastro.auth.domain.ports import SessionRepository


async def test_get_by_hashed_token_reads_back_every_field_that_add_wrote(
    sessions: SessionRepository, read_sessions: SessionRepository, session: Session
) -> None:
    await sessions.add(session)

    assert await read_sessions.get_by_hashed_token(session.hashed_token) == session


async def test_get_by_hashed_token_answers_none_for_an_unknown_session(
    sessions: SessionRepository, session: Session
) -> None:
    assert await sessions.get_by_hashed_token(session.hashed_token) is None


async def test_two_next_id_calls_return_two_different_ids(
    sessions: SessionRepository,
) -> None:
    assert await sessions.next_id() != await sessions.next_id()


async def test_remove_deletes_the_session(
    sessions: SessionRepository, read_sessions: SessionRepository, session: Session
) -> None:
    await sessions.add(session)

    await sessions.remove(session)

    assert await read_sessions.get_by_hashed_token(session.hashed_token) is None


async def test_remove_of_a_missing_session_raises_lookup_error_and_keeps_the_others(
    sessions: SessionRepository,
    read_sessions: SessionRepository,
    session: Session,
    earlier_session: Session,
) -> None:
    await sessions.add(session)

    with pytest.raises(LookupError, match=f"with the id {earlier_session.id.root}\\."):
        await sessions.remove(earlier_session)

    assert await read_sessions.get_by_hashed_token(session.hashed_token) == session


async def test_remove_expired_removes_an_expired_session_and_keeps_an_active_one(
    sessions: SessionRepository,
    read_sessions: SessionRepository,
    session: Session,
    earlier_session: Session,
) -> None:
    await sessions.add(session)
    await sessions.add(earlier_session)

    await sessions.remove_expired(at=session.expires_at - timedelta(seconds=1))

    assert await read_sessions.get_by_hashed_token(session.hashed_token) == session
    assert await read_sessions.get_by_hashed_token(earlier_session.hashed_token) is None


async def test_remove_expired_removes_a_session_that_expires_at_that_moment(
    sessions: SessionRepository, read_sessions: SessionRepository, session: Session
) -> None:
    await sessions.add(session)

    await sessions.remove_expired(at=session.expires_at)

    assert await read_sessions.get_by_hashed_token(session.hashed_token) is None


async def test_remove_expired_keeps_every_active_session_and_returns_0(
    sessions: SessionRepository,
    read_sessions: SessionRepository,
    session: Session,
    earlier_session: Session,
) -> None:
    await sessions.add(session)
    await sessions.add(earlier_session)

    removed = await sessions.remove_expired(
        at=earlier_session.expires_at - timedelta(seconds=1)
    )

    assert removed == 0
    assert await read_sessions.get_by_hashed_token(session.hashed_token) == session
    assert await read_sessions.get_by_hashed_token(earlier_session.hashed_token) == (
        earlier_session
    )


async def test_remove_expired_returns_the_number_of_removed_sessions(
    sessions: SessionRepository, session: Session, earlier_session: Session
) -> None:
    await sessions.add(session)
    await sessions.add(earlier_session)

    removed = await sessions.remove_expired(at=session.expires_at)

    assert removed == 2


async def test_a_field_assigned_with_no_update_keeps_its_stored_value(
    sessions: SessionRepository, read_sessions: SessionRepository, session: Session
) -> None:
    await sessions.add(session)
    added_expires_at = session.expires_at
    session.expires_at -= timedelta(days=1)
    read = await read_sessions.get_by_hashed_token(session.hashed_token)
    assert read is not None
    read.expires_at -= timedelta(days=1)

    stored = await read_sessions.get_by_hashed_token(session.hashed_token)

    assert stored is not None
    assert stored.expires_at == added_expires_at
