---
status: accepted
---

# Build on FastAPI, SQLAlchemy 2, and taskiq, in four layers joined by hand-written mappers

rastro builds on FastAPI, SQLAlchemy 2, and taskiq, and splits each app into four layers: domain, application, infrastructure, and presentation. The domain imports no framework other than Pydantic, a table stays a plain row of primitive columns, and FastAPI and SQLAlchemy appear only in the presentation and infrastructure layers. Each conversion between layers is a hand-written function that names every field, so mypy reports a renamed field at the mapper.

The FastAPI rewrite made one SQLModel class both the table and the entity of a User. That shape blurred the line between a table and a business rule:

- The `User` table held value object columns through a custom SQLAlchemy type, so the table knew the domain, and each new kind of value object needed a new column type.
- The Session lifetime and expiry lived in the Session store adapter until a code review moved them, because a table-shaped entity gives a rule no obvious home.
- Services received the `AsyncSession`, so the application code imported SQLAlchemy.
- SQLModel accepts a foreign key only as a string, so a renamed column fails at run time and not in mypy.

The layered `main` branch had its own costs, which the hand-written mappers avoid: five copies of the User field list across the aggregate, two DTOs, and three mapper classes, a generic `Mapper` base that mypy could not check field by field, and a `UseCase.execute(*args: Any) -> Any` base that turned mypy off.

## Considered options

- **SQLModel with the table as the entity (the FastAPI rewrite).** One class removes the mappers, but the table knows every value object, and a rule that reads two fields has no home outside the table or a service.
- **Django with layers (`main`).** This keeps the admin and `contrib.auth`. The Django model speaks Django and the value objects speak Pydantic, so code filled the gap between the two: three model field overrides, a form field, and a second translation of each Pydantic error. Its mappers were generic classes that mypy could not check.
- **Active Record.** The model saves itself and holds the rules, so no mapper exists. Every rule lands on the model, a rule that spans two models has no clear home, and a domain test needs the database.
- **Errors that carry their HTTP status.** One class holds everything about one error, but a domain error raised in a task then carries an HTTP status. Each app's presentation layer holds an error-to-status table in its place, and an architecture test fails when an error class has no row.
- **Celery, Dramatiq, or arq as the task queue.** Each needs a Redis or RabbitMQ server in the compose file before rastro has its first real task. taskiq is async like the views, and its broker is one module.

## Accept the cost of the mappers

A field crosses each layer through one mapper per pair of types, in the layer that owns the outer type: the infrastructure converts a row to an aggregate and back, and the application converts an aggregate to an Output DTO. A new field therefore costs one line in each mapper. The mappers are functions with typed arguments and keyword constructors, so mypy rejects a mapper that misses a required field or passes a field that a type no longer has. That check is what makes the cost acceptable: a forgotten field fails the build, and on `main` the generic `Mapper` base let it pass mypy.

A row, an aggregate, and a DTO use the same field names, so a mapper reads as a list of equal pairs, and a different name signals a different concept. An application DTO is both the request body and the use case contract until an edge needs a different shape, so the presentation layer needs no mapper while the shapes agree.

## Use ZeroMQ as the first taskiq broker

taskiq's ZeroMQ broker needs no server, so the compose file adds only a `worker` service, which runs with `-w 1`. The broker has three limits, and rastro accepts them until its first real task:

- With N workers, each task runs N times, because every worker receives every message.
- A task sent while the worker is down is lost, because ZeroMQ keeps no queue.
- There is no result backend, so a caller cannot read the result of a task.

Changing the broker changes one module.

## Consequences

- rastro owns what Django gave for free: the Session, the CSRF check, the password hash, and the timing of an unknown email. The admin and `createsuperuser` go away.
- A domain test is a function call with no database and no fake, a use case test runs with in-memory fake repositories, and only a repository test needs Postgres.
- The problems module is the only place that knows Pydantic's error types or builds a problem body.
- Mutable aggregates validate on assignment, so a use case changes a field by assignment and a repository writes it back with an explicit `update`. No identity map or change tracking crosses the mapper.
- The OpenTelemetry SQLAlchemy instrumentation, 0.66b1 at the time of writing, declares SQLAlchemy below 2.1, so `instrument_engine` skips its dependency check. Without the skip, the instrumentation logs the conflict and emits no query span.
- import-linter contracts, ruff rules, and pytest architecture tests check these rules, as `CODING_STANDARDS.md` describes.
