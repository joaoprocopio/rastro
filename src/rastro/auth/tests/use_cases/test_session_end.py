from datetime import timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.application.use_cases import session_end
from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.errors import NotAuthenticatedError
from rastro.auth.domain.value_objects import SessionToken
from rastro.auth.tests.fakes import FakeClock, FakeSessionRepository


async def test_it_ends_the_session_of_the_token_and_no_other(
    sessions: FakeSessionRepository,
    clock: FakeClock,
    ana: User,
    session_token: SessionToken,
) -> None:
    other = Session.start(
        id=await sessions.next_id(),
        user_id=ana.id,
        token=SessionToken(SecretStr("other")),
        at=clock.now(),
        lifetime=timedelta(seconds=1),
    )
    await sessions.add(other)

    await session_end(session_token, sessions=sessions, clock=clock)

    assert sessions.sessions == {other.id: other}


async def test_it_raises_not_authenticated_with_no_token(
    sessions: FakeSessionRepository, clock: FakeClock, session_token: SessionToken
) -> None:
    with pytest.raises(NotAuthenticatedError):
        await session_end(None, sessions=sessions, clock=clock)

    assert len(sessions.sessions) == 1


async def test_it_raises_not_authenticated_for_a_token_with_no_session(
    sessions: FakeSessionRepository, clock: FakeClock, session_token: SessionToken
) -> None:
    with pytest.raises(NotAuthenticatedError):
        await session_end(
            SessionToken(SecretStr("unknown")), sessions=sessions, clock=clock
        )

    assert len(sessions.sessions) == 1


async def test_it_raises_not_authenticated_for_an_expired_session(
    sessions: FakeSessionRepository, clock: FakeClock, session_token: SessionToken
) -> None:
    clock.current += timedelta(seconds=1)

    with pytest.raises(NotAuthenticatedError):
        await session_end(session_token, sessions=sessions, clock=clock)
