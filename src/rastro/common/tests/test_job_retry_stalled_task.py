from collections.abc import Awaitable, Callable
from datetime import timedelta

from procrastinate import App
from procrastinate.jobs import Status

from rastro.common.presentation.tasks import job_retry_stalled_task


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
