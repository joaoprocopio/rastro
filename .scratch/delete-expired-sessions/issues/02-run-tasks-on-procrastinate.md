# 02: Run the tasks on Procrastinate, and remove taskiq

**What to build:** every task of rastro runs on Procrastinate, and taskiq leaves the codebase. The sample app's tasks declare themselves on a Procrastinate `Blueprint` with `pass_context=True`, open their own transaction with `sessionmaker.begin()`, and read the sessionmaker through one typed accessor in the common presentation dependencies. That accessor replaces `task_sessionmaker`. The worker module builds the `App` with the `PsycopgConnector`, from the existing Postgres URL setting in libpq form. It also passes the sessionmaker in the `additional_context` of its `worker_defaults` and adds the blueprint of every app that has a tasks module. `create_app` drops its `broker` parameter, and the API opens no Procrastinate app.

These items go: the taskiq dependency with its `opentelemetry` and `zmq` extras, the broker module, the ZeroMQ settings with their lines in `.env.example` and the compose file, and `instrument_broker`. The compose `worker` service and the README run the Procrastinate worker. The task section of `CODING_STANDARDS.md` states the blueprint, the context accessor, and the at-least-once rule. The same file drops the ZeroMQ limits, the `.kiq(...)` sentence of the view rule, and `create_broker` from the telemetry section. The spec is `.scratch/delete-expired-sessions/spec.md`.

**Blocked by:** 01

**Status:** resolved

- [x] With Procrastinate's `InMemoryConnector`, a sample task that succeeds commits its writes.
- [x] With Procrastinate's `InMemoryConnector`, a sample task that raises rolls back its writes.
- [x] No module imports `taskiq`, and the project dependencies hold no taskiq package.
- [x] The settings and `.env.example` hold no ZeroMQ setting.
- [x] The test that a task produces a span and the test that the app starts its broker are gone.
- [x] `docker compose up worker` starts the Procrastinate worker, and it connects to Postgres.
- [x] mypy strict accepts the accessor and every task with no `Any` and no ignore comment.
- [x] Every check in the README passes.
