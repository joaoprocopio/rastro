from procrastinate import Blueprint, JobContext

blueprint = Blueprint()


@blueprint.periodic(cron="* * * * *", periodic_id="job_retry_stalled")
@blueprint.task(pass_context=True)
async def job_retry_stalled_task(context: JobContext, timestamp: int) -> None:
    job_manager = context.app.job_manager
    for job in await job_manager.get_stalled_jobs():
        await job_manager.retry_job(job)
