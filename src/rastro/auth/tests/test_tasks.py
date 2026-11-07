import logging

import pytest
from procrastinate import App
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import Session
from rastro.auth.infrastructure.repositories import SqlSessionRepository
from rastro.auth.presentation import tasks
from rastro.auth.presentation.tasks import session_remove_expired_task


async def test_the_task_removes_the_expired_session_and_logs_the_count(
    worker_app: App,
    reader: AsyncSession,
    active_session: Session,
    expired_session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The task reads the wall clock, as the two Session fixtures do.
    deferrer = session_remove_expired_task.configure(task_kwargs={"timestamp": 0})
    await deferrer.defer_async()

    with caplog.at_level(logging.INFO, logger=tasks.__name__):
        await worker_app.run_worker_async()

    read_sessions = SqlSessionRepository(reader)
    assert await read_sessions.get_by_hashed_token(active_session.hashed_token) == (
        active_session
    )
    assert await read_sessions.get_by_hashed_token(expired_session.hashed_token) is None
    (record,) = [record for record in caplog.records if record.name == tasks.__name__]
    assert record.getMessage() == "Expired Sessions removed: 1"
