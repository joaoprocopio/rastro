from collections.abc import Awaitable, Callable
from typing import Any, cast

from procrastinate import Blueprint, JobContext
from procrastinate.tasks import Task
from procrastinate.types import JSONDict
from sqlalchemy.ext.asyncio import AsyncSession

blueprint = Blueprint()


# configure().defer_async takes any JSON, so this helper restores the task signature.
def defer_in_transaction[**P](
    task: Task[Any, Any, P], *, db_session: AsyncSession
) -> Callable[P, Awaitable[int]]:
    async def defer(*args: P.args, **kwargs: P.kwargs) -> int:
        # Procrastinate drops a positional argument, and the job would then fail.
        if args:
            raise TypeError(f"A job of {task.name} takes keyword arguments only.")
        connection = await db_session.connection()
        raw_connection = await connection.get_raw_connection()
        # With no connection, Procrastinate would commit the job on its own pool.
        if raw_connection.driver_connection is None:
            raise RuntimeError("The transaction of the job holds no connection.")
        deferrer = task.configure(
            connection=raw_connection.driver_connection,
            task_kwargs=cast(JSONDict, kwargs),
        )
        return await deferrer.defer_async()

    return defer


@blueprint.periodic(cron="* * * * *")
@blueprint.task(pass_context=True)
async def job_retry_stalled_task(context: JobContext, timestamp: int) -> None:
    job_manager = context.app.job_manager
    for job in await job_manager.get_stalled_jobs():
        await job_manager.retry_job(job)
