---
status: accepted
---

# Run tasks with Procrastinate on the app's Postgres, and make every task idempotent

rastro runs its tasks with Procrastinate in place of taskiq. Procrastinate stores each job as a row in rastro's own Postgres, so a use case defers a job in the transaction that writes its rows, and a rollback removes the job with the rows. Durability decides the choice: a broker outside Postgres cannot commit with the app, so a crash between the commit and the publish loses the task unless rastro writes an outbox. Every queue in this comparison delivers a job at least once, so each task takes IDs, reads its state from the database, and does nothing on a second run.

This decision replaces the taskiq part of ADR 0001: the taskiq option in its considered options and its section "Use ZeroMQ as the first taskiq broker".

## Evidence from the failure prototypes

On 2026-10-31 two throwaway prototypes ran real worker processes, `kill -9`, and container restarts, and counted every execution in Postgres. Procrastinate 3.10.0 passed all seven scenarios:

- A rollback of an `AsyncSession` transaction removed the deferred job, and another connection saw no job before the commit.
- A job whose worker got `kill -9` stayed `doing` until a periodic task retried it, 51.6s after the kill. It started twice and finished once.
- 100 jobs deferred with no worker running each ran once when a worker started.
- With `NOTIFY` off, polling started each job within 5s.
- Two workers ran a cron task once per tick, and after a 3-minute outage only the latest missed tick ran.
- 10,000 jobs drained in 38.8s with 2 workers at concurrency 10, and each ran once.

taskiq 0.13.0 with taskiq-aio-pika 0.6.1 on RabbitMQ 4.4.0 delivered well: quorum queues kept 100 messages across a broker restart, a killed worker's task came back 0.3s after a new worker started, and `.kiq()` raised `SendTaskError` while the broker was down. Its scheduler failed: a tick was lost while the scheduler was down, two schedulers ran each tick twice, and a restart inside one minute ran the cron twice with one scheduler. A task longer than the RabbitMQ `consumer_timeout` ran three times in parallel.

## Considered options

- **taskiq with RabbitMQ.** Delivery passed every test, but `.kiq()` cannot join the app's transaction, the scheduler keeps its state in memory with no lock, and one maintainer wrote 22 of the 23 commits of taskiq-aio-pika in the last 12 months.
- **taskiq with Redis Streams.** Redis with `appendfsync everysec` can lose the last second of writes, `maxmemory` eviction can drop messages, and `ListRedisScheduleSource` serializes schedules with pickle by default.
- **taskiq-postgres 0.9.1.** It delivers a message only through `NOTIFY` and never reads a `pending` or `processing` row again, so a message sent while the worker is down, or held by a killed worker, never runs.
- **DBOS.** It checkpoints each workflow step in Postgres, but each task becomes a workflow of steps, its system database I/O runs in threads, and recovery across hosts needs the paid Conductor or a fixed executor ID per host.
- **Temporal and Hatchet.** Both add a server that rastro must operate.
- **RQ, Celery, Huey, and Dramatiq.** None has an asyncio enqueue and worker.
- **arq, SAQ, pgqueuer, Absurd, and Oban for Python.** Each enqueues by task name or `Any`, so the type checker accepts a wrong argument.

## Consequences

- A use case defers a job through a helper that takes the psycopg connection of the `AsyncSession`. `Task.configure(...).defer_async` accepts any JSON keyword, so the helper restores the task signature, and mypy strict rejects a wrong or missing argument.
- `batch_defer_async` takes plain dicts, so a second helper builds each dict from the task signature.
- Procrastinate leaves a killed job in `doing`, so rastro runs a periodic task that retries stalled jobs. With the defaults, recovery takes up to about 95s: 30s without heartbeat, up to 60s until the cron, and up to 5s of polling.
- A cron schedule lives in the code. With every worker down, only the latest missed tick runs, and only within 10 minutes of its time.
- A worker fetches one job per query, so a bulk task processes a batch of rows per job.
- Procrastinate has no rate limit, so the concurrency of the workers on a queue sets the pace of outgoing email.
- A task whose effect stays in Postgres checks and applies the effect in one transaction, so a second run finds the work done. A task with an external effect, such as an email, sends an idempotency key when the provider accepts one. Otherwise it records whether a crash after the send retries the email or leaves it for review.
- An Alembic migration holds the Procrastinate schema, and the worker runs with N processes, because each job runs on one worker.
