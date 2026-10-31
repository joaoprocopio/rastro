import logging
from datetime import UTC, datetime, timedelta

import pytest
from procrastinate import App
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import SessionToken
from rastro.auth.infrastructure.repositories import SqlSessionRepository
from rastro.auth.presentation import tasks
from rastro.auth.presentation.tasks import session_remove_expired_task

ACTIVE_TOKEN = SessionToken(SecretStr("active"))
EXPIRED_TOKEN = SessionToken(SecretStr("expired"))


async def test_the_task_removes_the_expired_session_and_logs_the_count(
    task_app: App,
    db_session: AsyncSession,
    reader: AsyncSession,
    user: User,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The task reads the system clock, so the Sessions expire around the real time.
    now = datetime.now(UTC)
    sessions = SqlSessionRepository(db_session)
    for token, expires_at in [
        (ACTIVE_TOKEN, now + timedelta(days=1)),
        (EXPIRED_TOKEN, now - timedelta(days=1)),
    ]:
        await sessions.add(
            Session(
                id=await sessions.next_id(),
                user_id=user.id,
                hashed_token=token.digest(),
                expires_at=expires_at,
            )
        )
    await db_session.commit()
    job = session_remove_expired_task.configure(task_kwargs={"timestamp": 0})
    await job.defer_async()

    with caplog.at_level(logging.INFO, logger=tasks.__name__):
        await task_app.run_worker_async()

    read_sessions = SqlSessionRepository(reader)
    assert await read_sessions.get_by_hashed_token(ACTIVE_TOKEN.digest()) is not None
    assert await read_sessions.get_by_hashed_token(EXPIRED_TOKEN.digest()) is None
    (record,) = [record for record in caplog.records if record.name == tasks.__name__]
    assert record.getMessage() == "Expired Sessions removed: 1"
