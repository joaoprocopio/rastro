import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta

import pytest
from procrastinate import App
from procrastinate.jobs import Status
from procrastinate.testing import InMemoryConnector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.common.presentation.tasks import (
    defer_in_transaction,
    job_retry_stalled_task,
)
from rastro.common.tests.sample.domain.errors import NoteRejectedError
from rastro.common.tests.sample.presentation.tasks import (
    note_create_task,
    note_paint_task,
    note_reject_task,
)

pytestmark = pytest.mark.usefixtures("sample_tables")


async def test_a_task_that_succeeds_commits_its_writes(
    worker_app: App, note_count: Callable[[], Awaitable[int]]
) -> None:
    await note_create_task.defer_async()
    await worker_app.run_worker_async()

    assert await note_count() == 1


async def test_a_task_that_raises_rolls_back_its_writes(
    worker_app: App,
    note_count: Callable[[], Awaitable[int]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    await note_reject_task.defer_async()
    with caplog.at_level(logging.ERROR):
        await worker_app.run_worker_async()

    # The worker logs the error of a failed job in place of raising it.
    (record,) = caplog.records
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], NoteRejectedError)
    assert await note_count() == 0


@pytest.mark.usefixtures("unbound_worker_app")
async def test_a_job_commits_with_the_transaction_that_defers_it(
    sessionmaker: async_sessionmaker[AsyncSession], reader: AsyncSession
) -> None:
    async with sessionmaker.begin() as db_session:
        job_id = await defer_in_transaction(note_create_task, db_session=db_session)()

    jobs = await reader.execute(text("SELECT id, status FROM procrastinate_jobs"))
    assert [tuple(job) for job in jobs] == [(job_id, "todo")]


@pytest.mark.usefixtures("unbound_worker_app")
async def test_a_job_rolls_back_with_the_transaction_that_defers_it(
    sessionmaker: async_sessionmaker[AsyncSession], reader: AsyncSession
) -> None:
    with pytest.raises(NoteRejectedError):
        async with sessionmaker.begin() as db_session:
            await defer_in_transaction(note_create_task, db_session=db_session)()
            raise NoteRejectedError()

    jobs = await reader.execute(text("SELECT id FROM procrastinate_jobs"))
    assert list(jobs) == []


async def test_a_deferred_job_keeps_the_arguments_that_its_task_declares(
    worker_app: App, db_session: AsyncSession
) -> None:
    job_id = await defer_in_transaction(note_paint_task, db_session=db_session)(
        color="yellow"
    )

    connector = worker_app.connector
    assert isinstance(connector, InMemoryConnector)
    assert connector.jobs[job_id]["args"] == {"color": "yellow"}


async def test_a_positional_argument_raises_in_place_of_a_job_that_would_fail(
    worker_app: App, db_session: AsyncSession
) -> None:
    defer = defer_in_transaction(note_create_task, db_session=db_session)

    with pytest.raises(TypeError, match="takes keyword arguments only"):
        await defer(0)  # type: ignore[call-arg]


async def test_a_job_whose_worker_sent_no_heartbeat_for_over_30_seconds_is_todo_again(
    worker_app: App, doing_job: Callable[[timedelta], Awaitable[int]]
) -> None:
    job_id = await doing_job(timedelta(seconds=31))
    await job_retry_stalled_task.configure(task_kwargs={"timestamp": 0}).defer_async()
    # The worker skips the `stalled` queue, so the retried job waits as `todo`.
    await worker_app.run_worker_async(queues=["default"])

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.TODO


async def test_a_job_whose_worker_sends_heartbeats_stays_doing(
    worker_app: App, doing_job: Callable[[timedelta], Awaitable[int]]
) -> None:
    # A worker sends a heartbeat every 10 seconds.
    job_id = await doing_job(timedelta(seconds=10))
    await job_retry_stalled_task.configure(task_kwargs={"timestamp": 0}).defer_async()
    await worker_app.run_worker_async(queues=["default"])

    assert await worker_app.job_manager.get_job_status_async(job_id) == Status.DOING
