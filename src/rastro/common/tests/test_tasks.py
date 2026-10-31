import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta

import pytest
from procrastinate import App
from procrastinate.jobs import Status

from rastro.common.presentation.tasks import job_retry_stalled_task
from rastro.common.tests.sample.domain.errors import NoteRejectedError
from rastro.common.tests.sample.presentation.tasks import (
    note_create_task,
    note_reject_task,
)

pytestmark = pytest.mark.usefixtures("sample_tables")


async def test_a_task_that_succeeds_commits_its_writes(
    task_app: App, note_count: Callable[[], Awaitable[int]]
) -> None:
    await note_create_task.defer_async()
    await task_app.run_worker_async()

    assert await note_count() == 1


async def test_a_task_that_raises_rolls_back_its_writes(
    task_app: App,
    note_count: Callable[[], Awaitable[int]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    await note_reject_task.defer_async()
    with caplog.at_level(logging.ERROR):
        await task_app.run_worker_async()

    # The worker logs the error of a failed job in place of raising it.
    (record,) = caplog.records
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], NoteRejectedError)
    assert await note_count() == 0


async def test_a_job_whose_worker_sent_no_heartbeat_for_over_30_seconds_is_todo_again(
    task_app: App, doing_job: Callable[[timedelta], Awaitable[int]]
) -> None:
    job_id = await doing_job(timedelta(seconds=31))
    await job_retry_stalled_task.configure(task_kwargs={"timestamp": 0}).defer_async()
    # The worker skips the `stalled` queue, so the retried job waits as `todo`.
    await task_app.run_worker_async(queues=["default"])

    assert await task_app.job_manager.get_job_status_async(job_id) == Status.TODO


async def test_a_job_whose_worker_sends_heartbeats_stays_doing(
    task_app: App, doing_job: Callable[[timedelta], Awaitable[int]]
) -> None:
    # A worker sends a heartbeat every 10 seconds.
    job_id = await doing_job(timedelta(seconds=10))
    await job_retry_stalled_task.configure(task_kwargs={"timestamp": 0}).defer_async()
    await task_app.run_worker_async(queues=["default"])

    assert await task_app.job_manager.get_job_status_async(job_id) == Status.DOING
