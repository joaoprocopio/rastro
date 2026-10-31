# 03: Run again a job whose worker died

**What to build:** a job whose worker died runs again within about 95 seconds. Procrastinate leaves the job of a killed worker in `doing`, so a periodic task in the common app's tasks module runs every minute. It calls `get_stalled_jobs()` with its defaults and `retry_job` for each job that it returns. The prototype for ADR 0004 used this body, with the decorators trimmed:

```python
async def retry_stalled_jobs(context: JobContext, timestamp: int) -> None:
    job_manager = context.app.job_manager
    for job in await job_manager.get_stalled_jobs():
        await job_manager.retry_job(job)
```

The spec is `.scratch/delete-expired-sessions/spec.md`.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Given a job in `doing` whose worker sent no heartbeat for more than 30 seconds, when the periodic task runs, then the job is `todo` again.
- [ ] Given a job in `doing` whose worker sends heartbeats, when the periodic task runs, then the job stays `doing`.
- [ ] The worker registers the periodic task on the cron `* * * * *`.
- [ ] Every check in the README passes.
