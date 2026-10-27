from datetime import timedelta

import pytest
from pydantic import SecretStr

from rastro.auth.application.dtos import SessionGetOutput
from rastro.auth.application.use_cases import session_get
from rastro.auth.domain.errors import NotAuthenticatedError
from rastro.auth.domain.value_objects import DisplayName, Email, SessionToken
from rastro.auth.tests.fakes import FakeClock, FakeSessionRepository, FakeUserRepository


async def test_it_returns_the_user_of_the_session(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    clock: FakeClock,
    session_token: SessionToken,
) -> None:
    output = await session_get(
        session_token, users=users, sessions=sessions, clock=clock
    )

    assert output == SessionGetOutput(
        email=Email("ana@x.com"), display_name=DisplayName("Ana")
    )


async def test_it_raises_not_authenticated_with_no_token(
    users: FakeUserRepository, sessions: FakeSessionRepository, clock: FakeClock
) -> None:
    with pytest.raises(NotAuthenticatedError):
        await session_get(None, users=users, sessions=sessions, clock=clock)


async def test_it_raises_not_authenticated_for_a_token_with_no_session(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    clock: FakeClock,
    session_token: SessionToken,
) -> None:
    with pytest.raises(NotAuthenticatedError):
        await session_get(
            SessionToken(SecretStr("unknown")),
            users=users,
            sessions=sessions,
            clock=clock,
        )


async def test_it_raises_not_authenticated_at_the_expiry_of_the_session(
    users: FakeUserRepository,
    sessions: FakeSessionRepository,
    clock: FakeClock,
    session_token: SessionToken,
) -> None:
    clock.current += timedelta(seconds=1)

    with pytest.raises(NotAuthenticatedError):
        await session_get(session_token, users=users, sessions=sessions, clock=clock)
