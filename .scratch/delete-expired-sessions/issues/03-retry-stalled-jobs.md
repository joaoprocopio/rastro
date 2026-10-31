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

**Status:** resolved

- [x] Given a job in `doing` whose worker sent no heartbeat for more than 30 seconds, when the periodic task runs, then the job is `todo` again.
- [x] Given a job in `doing` whose worker sends heartbeats, when the periodic task runs, then the job stays `doing`.
- [x] The worker registers the periodic task on the cron `* * * * *`.
- [x] Every check in the README passes.

## Comments

- The task is named `job_retry_stalled_task`, after the `<entity>_<action>_task` rule of `CODING_STANDARDS.md`, in place of the prototype name `retry_stalled_jobs`.
- `src/rastro/common/tests/test_job_retry_stalled_task.py` verifies the first two criteria, and no test verifies the cron. A worker with `wait=False` can stop before its periodic deferrer runs, and the periodic registry is a Procrastinate internal. On 2026-10-31, `procrastinate --app=rastro.worker.app worker` ran for 150s on a migrated scratch database and deferred the task at 16:40, 16:41, and 16:42. Its first run moved a planted job, whose worker heartbeat was 60s old, from `doing` back to `todo`, and the worker then ran that job to `succeeded`.
