# Run tasks on Procrastinate, and remove each expired Session every hour

Status: ready-for-agent
Type: feature

## Problem Statement

A User signs in from a browser and never ends the Session. The Session's lifetime runs out, but its row stays in `auth_session` forever, because no code removes an expired Session. Each sign-in adds one row, so the table grows with every Session that a client abandons.

rastro cannot run that cleanup reliably today. Its tasks run on taskiq with the ZeroMQ broker, which loses a task sent while the worker is down, runs each task once per worker, and has no scheduler process. ADR 0004 replaces taskiq with Procrastinate, so this spec moves the task runtime to Procrastinate and adds the cleanup as its first real task.

## Solution

Procrastinate replaces taskiq in every process. Each job is a row in rastro's own Postgres, so a job sent while the worker is down waits for it, and the worker runs each job once even with several workers. A cron schedule in the code starts a periodic task every hour, and that task removes every Session whose lifetime has run out, with the same rule as `Session.is_active`. The task writes the number of removed Sessions to the log.

## User Stories

1. As an operator, I want every expired Session removed within about an hour of its expiry, so that `auth_session` holds only Sessions that a client can still use.
2. As an operator, I want the cleanup to run without a scheduler process, so that the stack has no extra service to deploy and watch.
3. As an operator, I want the cleanup to run once per tick with several workers, so that scaling the worker never repeats it.
4. As an operator, I want a tick that the workers miss while they are down to run when they come back within 10 minutes, so that a short deploy does not skip the cleanup.
5. As an operator, I want a missed cleanup to cost nothing more than a delay, so that the next tick removes the rows that the missed tick left.
6. As an operator, I want the log to show how many Sessions each run removed, so that I can see the cleanup work in Grafana.
7. As an operator, I want a run that finds no expired Session to succeed and log zero, so that an empty run never looks like a failure.
8. As an operator, I want a job whose worker died to run again, so that a `kill -9` or an out-of-memory kill never leaves a job stuck.
9. As an operator, I want a job that a worker never started to wait in Postgres, so that a worker restart loses no work.
10. As an operator, I want the Procrastinate tables created by `alembic upgrade head`, so that one command migrates every table of rastro.
11. As an operator, I want the migrations to stay the same when the Procrastinate package changes, so that an old migration never changes under me.
12. As an operator, I want the stack to need no broker server, so that Postgres is the only stateful service of rastro.
13. As an operator, I want the ZeroMQ settings gone from the settings and the compose file, so that no unused setting remains.
14. As a User, I want my active Session untouched by the cleanup, so that I am never signed out before my Session's lifetime runs out.
15. As a User, I want a Session whose lifetime ran out to stay unusable, so that the cleanup changes nothing that I can see.
16. As a developer, I want a task to declare itself on a blueprint, so that a tasks module imports no Procrastinate app and a change of runtime stays in one module.
17. As a developer, I want a task to read its sessionmaker through one typed accessor, so that mypy strict checks every task.
18. As a developer, I want a task to open its own transaction in its body, so that a failed commit fails the job and Procrastinate retries or records it.
19. As a developer, I want task tests to run against Procrastinate's in-memory connector, so that a task test needs no worker process.
20. As a developer, I want the sample app's task tests to keep proving commit on success and rollback on failure, so that the task rules stay checked after the change of runtime.
21. As a developer, I want `CODING_STANDARDS.md` to describe the Procrastinate task rules, so that the next task follows them.
22. As a developer, I want the at-least-once rule written down, so that every new task reads its state from the database and does nothing on a second run.
23. As a developer, I want `create_app` to stop taking a broker, so that the API builds with no task runtime while no view sends a task.
24. As a developer, I want the README to show the new worker command, so that I can run the tasks locally.
25. As a maintainer, I want ADR 0001 to describe the current stack, so that a reader of 0001 does not learn about a broker that rastro no longer uses.
26. As a maintainer, I want the reason for Procrastinate and the prototype evidence to stay in ADR 0004 only, so that each meaning has one source.
27. As a maintainer, I want a later upgrade of Procrastinate to follow a written procedure, so that the next person copies the right SQL in the right order.

## Implementation Decisions

### Task runtime

- Procrastinate 3.10.0 replaces taskiq in every process. The taskiq dependency goes, with its `opentelemetry` and `zmq` extras, and so do the broker module, the ZeroMQ settings, their lines in `.env.example`, and their environment variables in the compose file.
- The Procrastinate app uses the `PsycopgConnector`. Its connection string comes from the existing Postgres URL setting, in libpq form, so the change adds no setting.
- Each app's tasks module declares its tasks and its periodic tasks on a Procrastinate `Blueprint`. The worker module builds the `App`, adds the blueprint of every app that has a tasks module, and keeps using `import_every_app_module`.
- The worker module passes the sessionmaker to every job through the app's `worker_defaults` and its `additional_context`. A task declares `pass_context=True`, and one typed accessor in the common presentation dependencies reads the sessionmaker from the `JobContext`. This accessor replaces `task_sessionmaker`, and it narrows the untyped `additional_context` value so that mypy strict accepts it.
- A task keeps the current rules: an `async def` named `<entity>_<action>_task` that opens its own transaction with `sessionmaker.begin()`, builds its repositories with the `dependencies` factories, and calls one use case. The transaction stays in the body because Procrastinate has no dependency injection, and a failed commit must fail the job.
- `create_app` drops its `broker` parameter, and the API opens no Procrastinate app. No view sends a task today. The first use case that sends a task adds the transactional enqueue helper from ADR 0004.
- The compose `worker` service runs the Procrastinate worker on the worker module's app. The comment and the `-w 1` limit of ZeroMQ go.
- Telemetry: `instrument_broker` goes, and no span wraps a task. The worker still calls `instrument` and `instrument_engine`, so its query spans and its log records still reach the collector, with no parent task span.

### Procrastinate schema

- One Alembic migration creates the Procrastinate schema. It holds a frozen copy of the `schema.sql` that ships in Procrastinate 3.10.0 and runs it with `op.execute`. The migration never reads the installed package, so an upgrade of the package changes no existing migration.
- The Alembic environment ignores every table, function, and type whose name starts with `procrastinate_`, so `compare_metadata` against `Row.metadata` still reports no difference.
- Upgrade procedure, written in `CODING_STANDARDS.md`: for each file in the package's `sql/migrations/` between the old version and the new one, add an Alembic migration with its SQL. A file whose name holds `pre` runs before the deploy of the new code, and a file whose name holds `post` runs after every worker runs the new code.

### Stalled jobs

- A periodic task in the common app's tasks module runs every minute. It calls `get_stalled_jobs()` with its defaults and `retry_job` for each job that it returns. Procrastinate leaves the job of a killed worker in `doing`, and without this task that job never runs again.
- The prototype for ADR 0004 used this body, with the decorators trimmed:

```python
async def retry_stalled_jobs(context: JobContext, timestamp: int) -> None:
    job_manager = context.app.job_manager
    for job in await job_manager.get_stalled_jobs():
        await job_manager.retry_job(job)
```

### Removal of expired Sessions

- The `SessionRepository` port gains `async def remove_expired(self, *, at: datetime) -> int`. The Sql adapter runs one `DELETE` of every row whose `expires_at <= at` and returns the number of deleted rows. The fake applies the same rule.
- The rule mirrors `Session.is_active`, which holds a Session active only while `at < expires_at`. A Session whose `expires_at` equals `at` is expired, so the cleanup removes it.
- The use case `session_remove_expired` takes the `sessions` repository and the `clock` as keyword-only ports, reads the time once from `Clock.now()`, calls `remove_expired`, and returns a `SessionRemoveExpiredOutput` with the count.
- The task `session_remove_expired_task` lives in the auth tasks module on the cron `0 * * * *`. It writes the count to the log with the standard library logger. The task carries no retry strategy, because the next tick does the same work.
- The cleanup removes a Session at the first tick after its expiry, with no retention period. A history of sign-ins, if rastro ever needs one, is a separate concept.
- The `DELETE` is one statement per run, with no batches and no index on `expires_at`.
- The race with the planned renewal of a Session is settled in the edge cases of idea 0002: the renewal updates only a row whose `expires_at` is still in the future, and an update that changes no row answers `401 auth.not_authenticated`.

### Documentation

- ADR 0001 is rewritten in place. Its title names FastAPI, SQLAlchemy 2, and Procrastinate, its taskiq option and its ZeroMQ section go, and one line points to ADR 0004 for the choice of the task queue. ADR 0004 keeps the reason and the prototype evidence.
- `CODING_STANDARDS.md` replaces every taskiq rule: the ZeroMQ limits go, and the task section states the blueprint, the context accessor, the at-least-once rule, and the schema upgrade procedure. The view rule drops its sentence about `.kiq(...)`, and the telemetry section drops `create_broker`.
- The README replaces the taskiq worker command with the Procrastinate worker command.

## Testing Decisions

- A good test checks behaviour that a caller sees: rows in the database, a returned count, a committed or rolled-back write. A test never asserts on SQL text, on a call to a fake, or on a Procrastinate internal.
- The `SessionRepository` behaviour suite, which runs each test with the fake and with the Sql adapter, covers `remove_expired`. The suite proves four behaviours: an expired Session goes, an active Session stays, a Session whose `expires_at` equals `at` goes, and the return value counts the removed Sessions. Prior art: the existing Session repository suite in the auth repository tests.
- A use case test calls `session_remove_expired` with the fake repository and `FakeClock`, and checks that the clock's time decides the removal and that the output holds the count. Prior art: the `session_end` use case tests.
- Task tests run the tasks through Procrastinate's `InMemoryConnector`, which replaces taskiq's `InMemoryBroker` in the fixtures. The sample app tests keep their two behaviours: a task that succeeds commits its writes, and a task that raises rolls them back. A new auth task test proves that `session_remove_expired_task` leaves only the active Session. Prior art: the common task tests and the sample app tasks.
- The migration tests prove that `alembic upgrade head` creates the Procrastinate tables and that `compare_metadata` still reports no difference. Prior art: the existing migration tests.
- Two tests go: the test that a task produces a span with its queries, because task spans are out of scope, and the test that the app starts and stops its broker, because `create_app` no longer takes one.
- Every check in the README passes: ruff, ruff format, mypy, lint-imports, and pytest.

## Out of Scope

- A span for each task, and the link from a request trace to a task. A later change may add a Procrastinate task middleware.
- The transactional enqueue helper and the typed batch helper from ADR 0004, until a use case sends a task.
- An index on `expires_at`, unless a measurement on the table shows the need.
- A change of the Session lifetime or of `session_end`.
- The renewal of a Session on use, which idea 0002 covers.
- A rate limit on any queue, a result backend, and named queues.
- An upgrade of Procrastinate past 3.10.0.

## Further Notes

- ADR 0004 holds the evidence from the failure prototypes of 2026-10-31. Procrastinate passed seven scenarios: a rollback removed the deferred job, a killed job came back through the stalled-job retry, jobs deferred with no worker all ran once, polling started jobs without `NOTIFY`, a cron ran once per tick with two workers, only the latest missed tick ran after an outage, and 10,000 jobs each ran once.
- With the defaults, a job of a killed worker runs again after up to about 95 seconds: 30 seconds with no heartbeat, up to 60 seconds until the retry task, and up to 5 seconds of polling, because a retried job sends no `NOTIFY`.
- Procrastinate delivers a job at least once. The cleanup is idempotent, because a second `DELETE` finds no row that the first one removed.
- This spec replaces `.scratch/ideas/0001-delete-expired-sessions.md`. Its edge case about ZeroMQ and its two open questions no longer apply.
