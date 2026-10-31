from datetime import timedelta

from pydantic import SecretStr

from rastro.auth.application.dtos import SessionRemoveExpiredOutput
from rastro.auth.application.use_cases import session_remove_expired
from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import SessionLifetime, SessionToken
from rastro.auth.tests.fakes import FakeClock, FakeSessionRepository

LIFETIME = SessionLifetime(timedelta(seconds=1))


async def test_it_removes_the_sessions_that_expired_at_the_time_of_the_clock(
    sessions: FakeSessionRepository, clock: FakeClock, ana: User
) -> None:
    active = Session.start(
        id=await sessions.next_id(),
        user_id=ana.id,
        token=SessionToken(SecretStr("active")),
        at=clock.now(),
        lifetime=LIFETIME,
    )
    expired = Session.start(
        id=await sessions.next_id(),
        user_id=ana.id,
        token=SessionToken(SecretStr("expired")),
        at=clock.now() - LIFETIME.root,
        lifetime=LIFETIME,
    )
    await sessions.add(active)
    await sessions.add(expired)

    output = await session_remove_expired(sessions=sessions, clock=clock)

    assert output == SessionRemoveExpiredOutput(count=1)
    assert sessions.sessions == {active.id: active}
