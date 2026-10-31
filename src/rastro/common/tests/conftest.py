from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from procrastinate import App
from procrastinate.testing import InMemoryConnector
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.common.tests.sample.infrastructure.models import NoteRow
from rastro.common.tests.sample.presentation.tasks import note_create_task


@pytest.fixture
def note_count(
    sessionmaker: async_sessionmaker[AsyncSession], sample_tables: None
) -> Callable[[], Awaitable[int]]:
    # A test reads the rows that a request or a task wrote, as the auth view tests do.
    async def count() -> int:
        async with sessionmaker() as db_session:
            count = await db_session.scalar(select(func.count()).select_from(NoteRow))
            if count is None:
                raise RuntimeError("COUNT returned no row.")
            return count

    return count


@pytest.fixture
def doing_job(task_app: App) -> Callable[[timedelta], Awaitable[int]]:
    """Start a job of the `stalled` queue on a worker whose last heartbeat is that old."""
    connector = task_app.connector
    assert isinstance(connector, InMemoryConnector)

    async def start(heartbeat_age: timedelta) -> int:
        job_id = await note_create_task.configure(queue="stalled").defer_async()
        worker_id = await task_app.job_manager.register_worker()
        await task_app.job_manager.fetch_job(queues=["stalled"], worker_id=worker_id)
        connector.workers[worker_id] = datetime.now(UTC) - heartbeat_age
        return job_id

    return start
