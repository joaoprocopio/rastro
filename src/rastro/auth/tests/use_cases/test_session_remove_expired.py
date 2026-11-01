from rastro.auth.application.dtos import SessionRemoveExpiredOutput
from rastro.auth.application.use_cases import session_remove_expired
from rastro.auth.domain.aggregates import Session
from rastro.auth.tests.fakes import FakeClock, FakeSessionRepository


async def test_it_removes_the_sessions_that_expired_at_the_time_of_the_clock(
    sessions: FakeSessionRepository,
    clock: FakeClock,
    active_session: Session,
    expired_session: Session,
) -> None:
    output = await session_remove_expired(sessions=sessions, clock=clock)

    assert output == SessionRemoveExpiredOutput(count=1)
    assert sessions.sessions == {active_session.id: active_session}
