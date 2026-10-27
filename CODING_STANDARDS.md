# Coding standards

These rules define how rastro code is structured. Other projects copy rastro's patterns, so every change follows these rules, and a change that breaks a rule on purpose updates this file in the same commit.

Use the domain terms from `GLOSSARY.md` in code, tests, and docs. ADR 0001 records why rastro builds on FastAPI, SQLAlchemy 2, and taskiq, in four layers joined by hand-written mappers.

## Validate at the edge, trust the core

An edge is any place where data enters the system from outside the process. The database is an edge, and so is the network. The edges in rastro are:

- a view, which parses the HTTP request;
- a mapper from a row to an aggregate, which parses each value object of the row;
- a task, which parses its arguments;
- a client for an external service, which parses the response.

Each edge parses its raw input into value objects once. Use cases accept only value objects, DTOs, and other validated types, never raw `str` or `dict` input, so they hold business rules only.

Three levels split the work:

- **Validation** checks the shape of one value in isolation, for example "this is an email" or "the name has at most 320 characters". It lives in a value object in the domain's `value_objects` module, and nowhere else.
- **Business rules** depend on the state of the system or on several fields. A rule that reads only the fields of one aggregate is a method of the aggregate, for example "a Session is active before `expires_at`". A rule that needs data from outside one aggregate lives in a use case, for example "the email is not in use".
- **Database constraints** (`unique`, `CheckConstraint`) are the last safety net. They never replace the two levels above.

These rules follow from the split:

- A `CheckConstraint` violation means that an edge let invalid data through. It is a bug, so it answers `500`.
- A `unique` violation is a business rule. The use case checks for the conflict, and the repository's `add` translates the `IntegrityError` that a concurrent write can still cause into the same named `BaseError` subclass. The repository raises the named error only when `error.orig` is a `psycopg.errors.UniqueViolation` on the constraint of that rule, for example `auth_user_email_key` for `EmailInUseError`, so any other `IntegrityError` still answers `500`.
- Every edge validates, the database included. A row that fails its value object raises an error when the mapper builds the aggregate. No code path skips validation for a source that it trusts.

## Raise in place of a fallback value

Application code holds no fallback value for a state that it does not expect: no `or ""`, no `.get(key, {})`, and no `getattr(obj, name, None)` for an attribute that must exist. The code raises, and the error reaches the observability platform as a `500`. For example, the `405` handler raises when Starlette's exception has no `Allow` header, in place of an answer with an empty header, and the problem handlers raise when an error class has no row in the error-to-status table. A default stays only where the absence is a valid state of the domain, for example an optional field of a DTO.

## Lay out an app in four layers

Each app is one context, and its package name is its app label, for example `auth`. An app has four layer packages with fixed module names, so a reader finds a concept in any app at the same place:

```text
<app>/
  domain/
    aggregates.py      # aggregates: data with the rules that read only their own fields
    value_objects.py   # value objects: the validation rules
    errors.py          # the BaseError subclasses of the app
    ports.py           # the Protocol of each repository and dependency
  application/
    use_cases.py       # one async function per operation
    dtos.py            # the Input and Output of each use case
    mappers.py         # aggregate to Output DTO
  infrastructure/
    models.py          # rows: plain SQLAlchemy tables
    mappers.py         # row to aggregate, and aggregate to row
    repositories.py    # one repository per aggregate
    adapters.py        # the other implementations of the ports
  presentation/
    dependencies.py    # the FastAPI dependency that builds each adapter
    views.py           # the router, the views, and the error-to-status table
    tasks.py           # the taskiq tasks
  tests/
```

An app creates a module when it has its first member. When a module grows too large to read in one pass, it becomes a package with one module per aggregate, and the package `__init__.py` re-exports the public names.

Dependencies point inward. The domain imports no other layer, and the application imports only the domain. The infrastructure imports only the domain. The presentation imports the application and the domain, and only its `dependencies` module imports the infrastructure, to build adapters.

`rastro/common/` holds the code that more than one app uses, in the same four layers: the bases and the shared value objects such as `Id` in `domain`, `DTO` in `application`, `Row`, the engine factory, the module importer, and the repository helpers `next_id` and `existing_row` in `infrastructure`, and the problems, the CSRF check, and the database session and settings dependencies in `presentation`. `rastro.common.domain.schemas` holds `Schema` and `RootSchema`, the bases of the other bases. The `rastro` package itself holds only the wiring: `settings.py`, `app.py` (`create_app`), `main.py` (the process entry that `fastapi run` loads), `broker.py` (`create_broker`), `worker.py` (the process entry that `taskiq worker` loads), `telemetry.py`, and `migrations/`.

The test sample app in `rastro/common/tests/sample/` is the reference for the four layers. It holds the `Note` aggregate, the `Color` value object, the `NoteRepository` port, the use cases, `NoteRow`, its mappers, `SqlNoteRepository`, the views, and the tasks.

## Choose the form of code

Every piece of code takes one of four forms, so a reader can tell what a class does from its kind:

- **Data** is a class: an aggregate, a value object, a DTO, an error, or a row. A data class receives no dependency, and its methods read only its own fields and their arguments. A `typing.NamedTuple` is data only as the result of a domain method that holds several values and no rule, such as `PasswordCheck` from `User.verify_password`. No edge parses it, so it needs no Pydantic validation.
- **A port** is a `typing.Protocol` in the domain's `ports` module, for each dependency that the core swaps between production and tests. A hasher, a clock, and each repository are ports.
- **An adapter** is a class that implements a port and holds configuration or a resource, which it receives once, in its constructor. A repository receives the `AsyncSession`. A fake is an adapter class in the app's tests package.
- **Everything else is a function**: a use case, a mapper, a view, a FastAPI dependency, and a task.

A class inherits only from a framework base (`pydantic.BaseModel`, SQLAlchemy's `DeclarativeBase`, `Exception`, `typing.NamedTuple`) or from a rastro base that carries configuration or declaration rules, such as `Aggregate` or `Row`. An adapter does not inherit its `Protocol`, and the code uses no `abc.ABC`, so a fake and a real adapter have the same standing. mypy checks conformance where a dependency function returns the adapter as the port type:

```python
def note_repository(db_session: DatabaseSession) -> NoteRepository:
    return SqlNoteRepository(db_session)
```

## Pick a Pydantic base by kind

Every Pydantic class in rastro subclasses a base of its kind, so it inherits one strict configuration and adds only what differs. Pydantic merges `model_config` from a base into its subclasses. No class is named `BaseModel`, so `BaseModel` always means Pydantic's class.

`rastro.common.domain.schemas` holds the two roots:

- `Schema` subclasses `pydantic.BaseModel` with `frozen`, `strict`, `from_attributes`, `extra="forbid"`, and `hide_input_in_errors`.
- `RootSchema[T]` subclasses `pydantic.RootModel` with `frozen`, `strict`, and `hide_input_in_errors`, because Pydantic rejects `extra` on a `RootModel`.

Each kind subclasses one of them:

- `Aggregate` in `rastro.common.domain.aggregates` subclasses `Schema` with `frozen` off and `validate_assignment` on. A use case changes a field by assignment, and `note.id = "2"` raises `ValidationError` at once. An aggregate method exists only when a change protects a rule across fields. `Aggregate` overrides no equality, so two aggregates are equal when every field is equal.
- `ValueObject` in `rastro.common.domain.value_objects` subclasses `Schema`, for a value object with several fields. Value objects stay frozen, so a value never changes under a reader.
- `RootValueObject[T]` in `rastro.common.domain.value_objects` subclasses `RootSchema[T]`, for a value object with one value.
- `DTO` in `rastro.common.application.dtos` subclasses `Schema`. It is the kind for every Input and Output of a use case, for the extensions of a request error, and for `Problem`.

`extra="forbid"` rejects an unknown key, so a misspelled optional field fails in place of being dropped. `hide_input_in_errors` keeps the input out of the message of a `ValidationError`, so a password or an email never reaches a log.

FastAPI parses the JSON of a body and then validates the Python result, so `strict` rejects a string for a field whose type is not `str` in Python, for example a `StrEnum`, a `datetime`, or a `UUID`. Such a field of a DTO declares `Field(strict=False)`:

```python
class PaintApplyInput(DTO):
    finish: Annotated[Finish, Field(strict=False)]
```

## Write value objects

A value object with one value is a `RootValueObject` in the domain's `value_objects` module, and code reads its value through `.root`. Each value object declares its rules with `Annotated` and `StringConstraints`, so one line holds one rule:

```python
class DisplayName(
    RootValueObject[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=320)]
    ]
):
    pass
```

A rule that `StringConstraints` cannot express, for example NFKC normalization, is a `BeforeValidator` that only transforms the value and never raises, so every rejection keeps the code of the rule that failed. Put the `BeforeValidator` before `StringConstraints` in `Annotated`. In the other order, Pydantic checks `pattern` before it applies `to_lower`, so `Email` would reject `Ana@x.com`.

An edge parses a raw value with `<ValueObject>.model_validate(value)`, which accepts a raw string or a built value object, and a DTO field typed with a value object parses its JSON with no adapter code. Each value object is its own class, so mypy rejects a raw `str` or another value object in a use case argument.

Every aggregate id is an `Id` from `rastro.common.domain.value_objects`, a `RootValueObject` over Pydantic's `PositiveInt`, so `User.id`, `Session.user_id`, and `Note.id` share one type, and a row with the id `0` fails when it becomes an aggregate. A future id kind that Python generates, for example a ULID, gets its own value object beside `Id`.

A value object equals only a value object of its own class, so `Id(1) == 1` is false. A test that compares an id with a column reads the `int` through `.root`.

An enum is a `StrEnum` in the domain's `value_objects` module. A domain module imports only the standard library, `pydantic`, and other domain modules of rastro.

## The frontend never validates

The frontend sends what the person typed and shows the errors that the backend returns. It runs no validation of its own, not even "required" or "minimum length", so each rule has one implementation. Every validation error from the backend points at its field and carries a stable problem type, so the frontend can show its own message next to the right input.

## Write use cases

A use case is an `async def` function in the application's `use_cases` module, and it holds the business rules that need data from outside one aggregate. Each use case follows these rules:

- The name is `<entity>_<action>`, for example `user_register` or `note_create`.
- The first argument is the Input DTO or value, when the operation has one. Every dependency follows as a required keyword-only argument typed with a port, so mypy finds every caller that a new dependency affects.
- It returns an Output DTO, a value object, or nothing.
- It reads the time from the `Clock` port and passes it to a domain method as a value, so a domain test passes a `datetime` and needs no fake clock.
- It creates a random secret with `secrets` and returns it, for example the Session token of `session_start`. A port wraps only a source that a test must control, such as the clock, and a test reads a random value from the return value of the use case.
- It never calls `commit` or `rollback`, because the edge owns the transaction.
- Every read goes through a use case and a repository that returns an aggregate, so a read has the same shape as a write.

```python
async def note_create(*, notes: NoteRepository) -> None:
    await notes.add(Note(id=await notes.next_id(), color=NEW_NOTE_COLOR))
```

A long parameter list is acceptable. Dependencies are never grouped into a bundle object, so the signature of each use case shows every dependency it uses.

A port describes the business operation as it is today, not a provider that may come later. When a swap changes the flow, for example from a password check to an OpenID Connect provider such as Keycloak, the port changes with it, and an ADR records the change. Telemetry is not a port: application code uses the OpenTelemetry API, which already separates the API from the SDK.

## Declare rows and repositories

A row is a plain SQLAlchemy 2 table with `Mapped` columns of primitive types, in the infrastructure's `models` module. Every row subclasses `Row` from `rastro.common.infrastructure.models`, a `DeclarativeBase` with no column, so each row declares its columns in its own body. The class takes the suffix `Row`, for example `NoteRow`. Each table name is `<app label>_<entity>`, for example `auth_user`. `user` is a reserved word in Postgres, so a hand-written `select * from user` returns the database user with no error.

- The `id` column is `bigint generated by default as identity`, declared as `mapped_column(BigInteger, Identity(), primary_key=True)`. A foreign key is `bigint` and references the column object, for example `ForeignKey(UserRow.id)`, so a rename fails mypy.
- `created_at` and `updated_at` are `DateTime(timezone=True)` with `server_default=func.now()`, and `updated_at` also sets `onupdate=func.now()`. Postgres sets them to the start time of the transaction, so no Python code reads a clock for audit data.
- A unique constraint that a repository translates is a `UniqueConstraint` in `__table_args__` with an explicit name, for example `USER_EMAIL_KEY` in `rastro/auth/infrastructure/models.py`, so the repository and the migration read one name.

`NoteRow` in `rastro/common/tests/sample/infrastructure/models.py` is the reference row. An architecture test requires that every mapped class subclasses `Row`, and that its table name starts with the label of its app.

A repository is an adapter class in the infrastructure's `repositories` module, one per aggregate, and its port lives in the domain's `ports` module. It receives the `AsyncSession` in its constructor, so the application layer never imports SQLAlchemy. Its methods follow Evans's names: `add`, `remove`, `update`, `get_by_id`, the other `get_by_*` lookups that use cases need, and `next_id`. A method takes the aggregate as its one positional argument, for example `notes.add(note)`.

- `next_id` calls `next_id` from `rastro.common.infrastructure.repositories` with the column object as `column`, for example `next_id(db_session, column=NoteRow.id)`. That function reads the table and the column names from the column object, calls `nextval` on the sequence of that column, and returns an `Id`, so every aggregate has its id from its creation and a renamed column fails mypy. Postgres never returns one value to two sessions, and a rolled-back transaction leaves a gap.
- `add` flushes, so that a constraint violation rises inside `add`.
- `update` and `remove` load the row through `existing_row` from `rastro.common.infrastructure.repositories`, which receives an `Id` and raises `LookupError` when no row has the id. `merge` alone inserts a missing row, so `update` loads the row before it calls `merge`. The load reads the identity map when the use case read the aggregate in the same transaction.
- `update` calls `merge` on the row that the mapper builds, and flushes. The mapper sets no audit column, so `merge` keeps `created_at` as stored, and `onupdate` sets `updated_at`.
- A `get_by_*` method returns the aggregate or `None`.

### Map between layers by hand

Each conversion between layers is a function that names every field, so mypy checks each one. The infrastructure's `mappers` module converts a row to an aggregate and an aggregate to a row. The application's `mappers` module converts an aggregate to an Output DTO. A row, an aggregate, and a DTO use the same field names, so a mapper reads as a list of equal pairs. A different name, or a value object that spans several columns, gets its conversion written in the same mapper.

A mapper from a row calls `model_validate` on each value object, because a row is an edge:

```python
def note_from_row(row: NoteRow) -> Note:
    return Note(id=Id.model_validate(row.id), color=Color.model_validate(row.color))
```

### Migrate the rows with Alembic

Alembic migrates the database, with autogenerate from `Row.metadata`. `migrations/env.py` imports the `infrastructure.models` module of every app with `import_every_app_module` from `rastro.common.infrastructure.modules`, so a new app needs no edit there. Create a migration with `uv run --env-file .env.example alembic revision --autogenerate -m "<what changes>"`, and read it before you commit it. The test `test_the_migrations_create_every_table_of_the_models` fails when a row changes without a migration.

## Build adapters in the presentation dependencies

Each route lists every adapter as an `Annotated[Port, Depends(factory)]` parameter, so the signature of a route shows every dependency that it uses. A factory in the presentation's `dependencies` module builds the adapter, and a test swaps it through `app.dependency_overrides`. A repository factory receives the request's `AsyncSession` through `DatabaseSession`, and a task calls the same factory with the session of its own transaction:

```python
@router.post("/notes", status_code=HTTPStatus.NO_CONTENT)
async def note_create_view(
    notes: Annotated[NoteRepository, Depends(note_repository)],
) -> None:
    await use_cases.note_create(notes=notes)
```

An adapter that several apps use, for example an SMTP mailer, lives in `rastro.common.infrastructure.adapters`, and each consumer app still declares its own port. In an app, only adapters and dependencies read `Settings`. A use case that needs a configuration value receives it through a port.


## Write views

A view is an `async def` function in the presentation's `views` module that handles one operation, named `<entity>_<action>_view`, for example `session_start_view`. Each app's views module holds one `APIRouter`, and `create_app` includes it under `/api/v1/<app label>/`. A command uses `POST` on a path that names the action, for example `POST /api/v1/auth/session/start`, and a query uses `GET`, for example `GET /api/v1/auth/session`. The view reads its input from typed parameters, calls one use case, and returns its Output DTO or nothing. It holds no business logic. A view never calls the body of a task.

Only the presentation layer uses FastAPI's `Depends`, so a use case runs the same in a view, a task, and a test. A dependency receives the database session through the `DatabaseSession` alias in `rastro.common.presentation.dependencies`:

```python
DatabaseSession = Annotated[AsyncSession, Depends(database_session, scope="function")]
```

`database_session` opens the `AsyncSession` inside `session.begin()`, so the request commits when the view returns and rolls back when an error rises. `scope="function"` is required: with FastAPI's default scope, the dependency exits after the response is sent, so a failed commit would follow a `2xx` response.

The DTOs of a use case subclass `DTO`, live in the application's `dtos` module, and are named `<Entity><Action>Input` and `<Entity><Action>Output`, for example `SessionStartInput`. Each DTO belongs to one operation, and no other operation reuses it, so an operation can change its format without breaking another one. FastAPI reads the Input DTO as the request body and the Output DTO as the response model, so the presentation needs no mapper while the HTTP shape and the use case contract agree. An application DTO holds no field that only one edge uses, and the first edge whose shape differs adds a presentation DTO.

A command view responds with no body: `201` when it creates something and `204` otherwise. FastAPI drops the body of a `204` only, so a `201` view declares `response_class=Response`, or FastAPI sends `null`. A query view responds with the `Output` DTO of its use case. A view that sets or deletes a cookie takes a `response: Response` argument and calls `set_cookie` or `delete_cookie` on it.

A view that only hands the client a value of the edge calls no use case, because no business rule and no row is involved. `csrf_set_view` is the one case: `GET /api/v1/auth/csrf` sets a new CSRF token through `csrf_cookie_set` in `rastro.common.presentation.views` and answers `204`. It uses `GET`, because the frontend fetches the token before its first change of state and `csrf_check` lets `GET` through.

### Read a request value in a dependency

A view reads a value outside the body, for example a cookie, through a dependency function in its presentation layer, and declares the alias once, as `rastro.common.presentation.dependencies` does for `DatabaseSession`:

```python
CurrentSessionToken = Annotated[SessionToken | None, Depends(_session_token)]
```

The dependency reads `request.cookies` and returns a value object, or `None` when the cookie is absent. It never declares a `Cookie`, `Query`, or `Header` parameter with a rule, because a parameter outside the body that fails validation answers `500`. The value object of such a value has no rule, so a bad value reaches the use case, and the use case answers it with its own error. For example, a token that no Session holds answers `auth.not_authenticated`.

## Start, read, and end a Session

A Session lives in the `auth_session` table, with `id`, `user_id`, `token_hash`, `created_at`, `updated_at`, and `expires_at`. The `Session` aggregate holds `id`, `user_id`, `token_hash`, and `expires_at`, and its rules read only these fields:

- `Session.start(id=..., user_id=..., token=..., at=...)` stores `token.digest()`, the SHA-256 digest of the token as a `SessionTokenHash`, and sets `expires_at` to `SESSION_LIFETIME` after `at`. The aggregate never holds the token, so no repository can store it, and a leaked database starts no Session.
- `session.is_active(at=...)` answers whether `at` is before `expires_at`. A Session ends `SESSION_LIFETIME` after it starts, 14 days from `rastro/auth/domain/aggregates.py`, with no renewal on use.
- `User.verify_password(password, hasher=...)` returns `PasswordCheck(is_correct, needs_rehash)`. It calls only `verify` and `needs_rehash` on the hasher, and the use case decides the effect.

`User.verify_password` types its `hasher` with the `PasswordHasher` port, and the ports module imports the aggregates, so `aggregates.py` imports the port under `if TYPE_CHECKING:`. Python 3.15 evaluates an annotation only when code reads it, and no code reads the annotations of a method at run time.

The use cases read the time from the `Clock` port:

- `session_start` gets the User by email and verifies the Credentials through `verify_password`. When `needs_rehash` is true, it assigns a new hash and calls `users.update`. It creates a Session token with `secrets.token_urlsafe(SESSION_TOKEN_BYTES)`, 32 random bytes, adds the Session, and returns the token. ADR 0002 records why the Session and the rehashed User share one transaction.
- For an unknown email, `session_start` verifies the password against `PasswordHasher.fixed_hash`, an argon2 hash of a random password, so the response takes as long as a wrong password. An unknown email and a wrong password raise the same `IncorrectCredentialsError`.
- `user_get_current` and `session_end` raise `NotAuthenticatedError` with no token, with a token that no Session holds, and when `clock.now()` reaches `expires_at`. Otherwise `user_get_current` returns the User of the Session as `UserGetCurrentOutput`, and `session_end` removes the Session.

`session_start_view` sets the token that the use case returns in the `rastro_session` cookie, which is `HttpOnly`, `Secure`, and `SameSite=Lax`, with a `Max-Age` of `SESSION_LIFETIME`. `session_end_view` deletes the cookie when the use case succeeds.

## Reject cross-site requests with a CSRF token

rastro checks a double-submit cookie on every request that changes state, so another site cannot act as a User. `GET /api/v1/auth/csrf` answers `204` and sets a new random token, 32 bytes from `secrets.token_urlsafe`, in the `rastro_csrf` cookie on each call. The cookie is `Secure` and `SameSite=Lax` with no `Max-Age`, and it is not `HttpOnly`, because the frontend reads it and sends it back in the `X-CSRF-Token` header.

`csrf_check` in `rastro/common/presentation/views.py` runs on every method that is not `GET`, `HEAD`, or `OPTIONS`, including `register` and `session/start`. It raises `CsrfFailedError`, which answers `request.csrf_failed` with `403`, when the cookie is absent or empty, when the header is absent, or when the two differ. It compares the bytes with `secrets.compare_digest`. Each views module declares the check on its router, so a new app cannot forget it:

```python
router = APIRouter(dependencies=[Depends(csrf_check)])
```

## Write tasks

A task is an `async def` function in the presentation's `tasks` module that the shared broker declares, named `<entity>_<action>_task`. A task is an edge: it parses its arguments into value objects, opens its own transaction, builds its repositories with the factories of the `dependencies` module, and calls one use case. It holds no business logic, and it never uses FastAPI's `Depends`:

```python
@async_shared_broker.task
async def note_create_task(
    sessionmaker: async_sessionmaker[AsyncSession] = TaskiqDepends(task_sessionmaker),
) -> None:
    async with sessionmaker.begin() as db_session:
        await note_create(notes=note_repository(db_session))
```

`task_sessionmaker` in `rastro.common.presentation.dependencies` reads the sessionmaker from the broker state, as `database_session` reads it from `app.state`. The task opens the transaction in its body, not in a `yield` dependency, because taskiq closes a dependency after it records the result of the task, so a failed commit would follow a successful task. The transaction commits when the block ends and rolls back when an error rises. A `BaseError` carries no HTTP status, so an error that a task raises holds nothing about HTTP.

A task declares itself on `async_shared_broker` from `taskiq`, never on the broker of rastro, so a tasks module imports no broker. `create_broker` in `rastro/broker.py` builds the broker and makes it the default broker of every shared task, so a change of broker changes that one module. The API sends a task with `<task>.kiq(...)`, and `create_app` starts and stops the broker in the lifespan of the app. `rastro/worker.py` imports the `presentation.tasks` module of every app with `import_every_app_module`, so a new task needs no edit there.

rastro uses taskiq's ZeroMQ broker, which needs no server, as ADR 0001 records. The API binds `RASTRO_ZEROMQ_PUBLISH_ADDRESS`, and the worker connects to `RASTRO_ZEROMQ_SUBSCRIBE_ADDRESS`. The broker has three limits:

- With N workers, each task runs N times, because every worker receives every message. The compose file runs one worker with `-w 1`.
- A task sent while the worker is down is lost, because ZeroMQ keeps no queue.
- There is no result backend, so a caller cannot read the result of a task.

The API binds the publish address, so it runs in one process: a second process cannot bind the same address.

## Trace requests, queries, and tasks

Every request, query, and task produces spans, which the collector writes to ClickHouse, where Grafana reads them. `rastro/telemetry.py` holds the wiring: `instrument` sets the OpenTelemetry providers and their exporters, and `instrument_app`, `instrument_engine`, and `instrument_broker` add the FastAPI, SQLAlchemy, and taskiq instrumentations. Each process entry calls `instrument` first and then the other three, as `rastro/main.py` and `rastro/worker.py` do, because each instrumentation reads the global provider. `create_app`, `create_database_engine`, and `create_broker` stay free of telemetry, so a test builds them with no exporter.

A span never holds personal data. The SQLAlchemy span keeps the statement with its placeholders and drops the parameters, so no email or password hash reaches ClickHouse. The FastAPI span keeps the method, the URL with its query string, the route, the status, the user agent, and the client address, and no other header and no body, so personal data never goes into a query string.

Application code uses the OpenTelemetry API, `opentelemetry.trace`, and never the SDK. Only `rastro/telemetry.py` and the root `conftest.py` import the SDK. The taskiq middleware puts the trace context in the labels of each message, so the span of a task joins the trace of the request that sent it. The worker reports `RASTRO_SERVICE_NAME` as `rastro-worker` in the compose file, so Grafana tells its spans from the spans of the API.

The compose file starts the collector before the API and the worker. At exit, each exporter flushes its queue to the collector, and with no collector the flush retries for the 10 seconds that `docker compose stop` waits, so Docker kills the process with exit code 137.

## Return errors as problem details

Every error response is an RFC 9457 problem with the media type `application/problem+json`. Its `type` is the error code, for example `auth.email_in_use`, a relative URI reference that RFC 3986 allows, and it is the identifier that a client reads: a frontend picks its own text from it, and an API consumer can look it up. Every problem carries `type` and `status`, and it omits `title`, `detail`, and `instance` when they have no value. A `404`, a `405`, and a `500` carry a `type` too:

```json
{"type": "request.not_found", "status": 404}
```

### Declare an error as a class

An error is a class that declares its code, so a domain error that a task raises carries no HTTP status. Each app declares its errors in the domain's `errors` module as subclasses of `BaseError` from `rastro.common.domain.errors`, and each class name ends in `Error`:

```python
class NoteRejectedError(BaseError):
    code = "common_sample.note_rejected"
```

A code has the form `<prefix>.<name>`. The prefix is the app label for the errors of an app, `request` for the errors of an HTTP request that every app shares, and `server` for a failure of rastro itself. The `request` and `server` errors live in `rastro.common.presentation.errors`, because only an HTTP request raises them.

`BaseError` checks each subclass when Python creates it. It raises `TypeError` when the subclass declares no `code`, when it declares a `status`, and when another class already declares the same code, and the message names both classes. A repeated code therefore fails at import time. An architecture test imports every `errors` module of rastro, so the check runs for every app, and it checks the `<prefix>.<name>` form.

An error with data declares its own extensions class and passes an instance to `BaseError.__init__`. The extensions of a domain error are a `ValueObject`, and the extensions of a request error are a `DTO`:

```python
class TooShortExtensions(DTO):
    min_length: int


class TooShortError(BaseError):
    code = "request.too_short"

    def __init__(self, extensions: TooShortExtensions) -> None:
        super().__init__(extensions)
```

An error without data passes none. `BaseError` declares no field that a single error needs, so a new error with data needs one class and no edit in the problems module. `MethodNotAllowedError` holds no method: the handler that answers a `405` copies the `Allow` header from Starlette's exception.

### Map each error to its status in a table

The presentation layer chooses the HTTP status of each error. Each app's presentation `views` module declares an `ERROR_STATUSES` table from error class to `HTTPStatus`, and `rastro.common.presentation.problems` declares the table of the `request` and `server` errors:

```python
ERROR_STATUSES: ErrorStatuses = {
    NoteRejectedError: HTTPStatus.CONFLICT,
}
```

`rastro/app.py` merges the tables into its own `ERROR_STATUSES` and passes it to `install_problem_handlers`. A new error therefore needs its class, a row in its app's table, and, for a new app, its table in the merge. The handlers read the status of the exact class, so a subclass of an error needs its own row. An error with no row raises `KeyError` in the handler, which answers `500`. An architecture test fails before that happens: it names each error class that has no row.

### Translate errors in the problems module

The problems module, `rastro.common.presentation.problems`, is the only translation layer in rastro. No other module builds a problem body or reads a Pydantic error type.

`Problem` holds the RFC 9457 members and an `extensions` member that serializes each of its keys at the top level of the object. `Problem` and `ValidationItem` share this mechanism through `ExtensibleDTO` in `rastro.common.application.dtos`. An extension named after a member of its class (for `Problem`, `type`, `status`, `title`, `detail`, or `instance`), or named against the RFC rule (a letter first, then only letters, digits, and `_`, with three characters at least), raises `ValueError` when the problem is built. `Problem.from_error(error, status=...)` copies the code and the extensions of the error and takes the status from the table, with no `match` on error classes.

### Answer a validation failure with typed items

A body that fails its DTO answers `422` with one item per failed field in `errors`:

```json
{
  "type": "request.validation_failed",
  "status": 422,
  "errors": [
    {"pointer": "#/color", "type": "request.too_short", "min_length": 3},
    {"pointer": "#/coats", "type": "request.invalid_type"}
  ]
}
```

`ValidationFailedError` holds its items in its extensions. A `ValidationItem` in `rastro.common.presentation.errors` holds `pointer`, `type`, and the extensions of the error of its rule, so it names no rule, and `ValidationItem.from_error(pointer=..., error=...)` builds it. The pointer is a JSON Pointer into the body. A malformed JSON body answers one `request.invalid_json` item with the pointer `#`, and a missing body answers one `request.field_required` item with the pointer `#`. An error on a parameter outside the body, for example a query parameter, raises `ValueError` and answers `500`, until a route needs that case.

One `match` in the problems module translates each Pydantic error type into a rastro error:

- `missing` is `FieldRequiredError`, `json_invalid` is `InvalidJsonError`, and `extra_forbidden` is `UnknownFieldError`.
- `string_too_short` and `too_short` are `TooShortError`, with `min_length` from the error's `ctx`.
- `string_too_long` and `too_long` are `TooLongError`, with `max_length` from the error's `ctx`.
- `string_pattern_mismatch` is `InvalidFormatError`, which has no extensions, so the pattern never reaches a response.
- Every other type is `InvalidTypeError`.

The `match` reads `ctx` only in the two length cases. No item shows the input value. A new rule with data needs an error class with its extensions and one case in this `match`.

### Register the problem handlers

`install_problem_handlers(app, error_statuses=...)` registers rastro's own exception handlers with the error-to-status table, and `create_app` calls it:

- FastAPI's `RequestValidationError` answers `request.validation_failed` with one validation item per Pydantic error, so FastAPI's own `422` body never reaches a client.
- `BaseError` answers the problem of the error, with the status of its row.
- Starlette's `HTTPException` answers `request.not_found` for a `404` and `request.method_not_allowed` with the `Allow` header for a `405`. Any other status raises again, and the next handler answers `500`.
- Any other exception answers `server.internal_error` with `500`. Starlette sends this response and then raises the exception again, so the server logs it.

## Configure settings

`Settings` in `rastro/settings.py` is a `pydantic-settings` class that reads environment variables, and each variable has the `RASTRO_` prefix, for example `RASTRO_POSTGRES_URL`. Every field except `postgres_url` has a default, so a local run needs only the database URL. A missing `RASTRO_POSTGRES_URL` or an invalid value stops the process at startup, and the error names the variable, not the field. The error hides the values that it read, so a password never reaches a log.

`RASTRO_POSTGRES_URL` has no default, so no password sits in the code. Its field is a `Secret` around a `PostgresDsn` that accepts only the scheme `postgresql+psycopg`, for example `postgresql+psycopg://postgres:postgres@localhost:5432/postgres`, so `repr` of the settings hides the password and another driver fails at startup. The engine factory, the Alembic environment, and the root `conftest.py` read the URL with `get_secret_value()`. A password with `@` or `/` needs percent-encoding in the URL. `compose.yaml` keeps the `POSTGRES_*` variables of the Postgres container, because the image reads them.

`RASTRO_SESSION_LIFETIME` reads an ISO 8601 duration, such as `P14D`, or a number of seconds. Each `SameSite` setting accepts only `lax`, `strict`, or `none`.

`.env.example` lists every variable with its local value, and a settings test fails when a variable is missing from it. A new setting needs a field with a default and a line in `.env.example`. `compose.yaml` sets the values of the stack. Run a local command with the local values through `uv run --env-file .env.example`.

`create_app` stores the settings on `app.state`, and the `AppSettings` alias in `rastro.common.presentation.dependencies` returns them to a view or a dependency. An HTTP test changes a setting through `app.dependency_overrides[app_settings]`.

`RASTRO_OPENAPI_ENABLED` decides whether FastAPI publishes `/openapi.json`, `/docs`, and `/redoc`. It defaults to `false`, so a deployment that forgets the variable shows no route list. `.env.example` turns it on for local runs.

## Test by layer

Each layer has its own kind of test, and a test passes fakes as arguments or through `app.dependency_overrides`, so no test uses `mock.patch` or `monkeypatch` on an adapter:

- **Domain tests** are pure and use no database and no fake. They check the normalization and rejection of each value object, with no input in the message of the `pydantic.ValidationError`, and each aggregate method. A domain method receives the time as a value, so the test passes a `datetime`.
- **Use case tests** call each use case with the in-memory fakes of the app's tests package, for example `FakeNoteRepository` in `rastro/common/tests/fakes.py`, which holds its aggregates in a `dict` by id. A fake `update` raises `LookupError` for a missing id, as the real repository does. A use case test asserts the error class with `pytest.raises`.
- **Repository tests** run each repository against the test database, inside the transaction that rolls back per test. They cover the mappers in both directions, `next_id` and the `Id` that it returns, a row with the id `0`, the translation of a unique violation, the `LookupError` of `update` for a missing row, and a corrupted row that fails when it becomes an aggregate. A test reads back through a second session, so the first session's identity map hides nothing.
- **View tests** cover the HTTP contract: status codes, bodies, headers, and cookies. A view test compares the literal JSON of each problem, because the literal is the contract that a client reads, and the view tests own the code of each rejection.
- **Task tests** send the task through taskiq's in-memory broker and read its rows in the database.

The `db_session` fixture of `rastro/auth/tests/conftest.py` opens an `AsyncSession` on the test connection, where each commit becomes a savepoint.

Tests run with `anyio` in auto mode, so an `async def` test needs no marker. The root `conftest.py` sets up the database and the HTTP client:

- `settings` reads `.env.example` and the environment, and names a new database `rastro_test_<random hex>`, so parallel runs share one Postgres server.
- `engine` creates that database, runs the Alembic migrations on it, and drops it at the end of the run.
- `connection` opens a transaction that rolls back at the end of each test, so tests share no rows.
- `sessionmaker` is bound to that connection. Each request or task transaction becomes a savepoint, so a commit and a rollback inside a request or a task behave as in production.
- `broker` is taskiq's `InMemoryBroker`, with the `sessionmaker` in its state, and the default broker of every shared task. `<task>.kiq()` runs the task to its end before it returns, so a task test needs no worker. A task that raises records its error in the result of `wait_result()`, not in `kiq()`.
- `password_hasher` is a `FakePasswordHasher` from `rastro/auth/tests/fakes.py`, which hashes a password to `fake$<password>` and records each hash and each verification. A hash with another scheme, for example `outdated$<password>`, needs a rehash.
- `clock` is a `FakeClock` at a fixed time, and a test moves the time with `clock.current`.
- `app` builds the app with the `sessionmaker` and the `broker`, and registers an `app.dependency_overrides` entry for every process-wide adapter, so no test runs a real one by accident. The `password_hasher` and `clock` factories return the fixtures of the same names. The repositories stay real. The `engine`, the `broker`, and the `app` go through the instrumentations of `rastro/telemetry.py`, so every test runs the production wiring.
- `spans` is an `InMemorySpanExporter`, emptied at the start of the test, that receives every span the test produces. The session fixture `span_exporter` sets it on the global tracer provider, because a process sets that provider once.
- `csrf_token` is a random CSRF token.
- `client` is an `httpx.AsyncClient` with `ASGITransport` against `app`, with the base URL `https://testserver`. It sends `csrf_token` in the `rastro_csrf` cookie and the `X-CSRF-Token` header, so a test that posts passes the CSRF check. A CSRF test deletes the header or the cookie from the client. A test of a `500` builds its own transport with `raise_app_exceptions=False`.

The `auth` test package has these fixtures in `rastro/auth/tests/conftest.py`:

- `user` is Ana, `ana@example.com`, a `User` that the fixture adds through `SqlUserRepository`, whose password `password` is hashed with `password_hasher`.
- `signed_in_client` is an HTTP client with the cookie of a Session of `user` and the CSRF token of `client`. The fixture adds the Session through `SqlSessionRepository`, so it sends no request.

The Session routes hash with argon2, so `rastro/auth/tests/views/conftest.py` overrides the `password_hasher` fixture with the argon2 hasher of `dependencies.password_hasher()`. The `user` of a view test can then sign in, and the register route of a view test writes an argon2 hash through the override of the `app` fixture. The same conftest overrides the `clock` fixture with the `SystemClock` of `dependencies.clock()`, because the view tests compare `expires_at` with the wall clock.

The `auth` app tests each operation by layer: `tests/test_aggregates.py` calls the aggregate methods, `tests/use_cases/` calls a use case with `FakeUserRepository`, `FakeSessionRepository`, `FakePasswordHasher`, and `FakeClock`, and `tests/repositories/` runs `SqlUserRepository` and `SqlSessionRepository` on the `db_session` fixture. `tests/use_cases/conftest.py` holds `users`, `sessions`, `ana` (a User in `users`), and `session_token` (the token of a Session of `ana` in `sessions`, which expires one second after `clock.now()`).

Before you write a test, look in the app's `tests/conftest.py` for a fixture that builds the state the test needs, and ask for it by name. When a second test needs the same state, add a fixture to that `conftest.py`, and keep the test file free of setup helpers. A fixture that more than one app uses lives in the root `conftest.py`. A test that needs a variation of the shared state calls the factory in the test, so the fixture set stays small. Test classes are optional, so group tests in a class only when the group helps the reader.

The test sample app in `rastro/common/tests/sample/` holds the four layers that a test of `rastro.common` needs, and its views and tasks call its use cases as the views and tasks of an app do. Its rows subclass `SampleRow`, an abstract `Row` with its own `MetaData`, so Alembic never migrates them, and the `sample_tables` fixture of `rastro/common/tests/conftest.py` creates them inside each test's transaction. The `sample_app` fixture includes the sample router and installs the problem handlers with the sample's error-to-status table merged into the table of `rastro/app.py`. The `note_count` fixture counts the `NoteRow` rows through a second session, so a test reads what a request or a task wrote, as the `auth` view tests read their rows. The worker never imports the sample tasks, because the sample is not an app of `rastro`.

## Check the architecture

Tools check these rules, and every change passes them before it merges, so a violation fails the check instead of waiting for a review:

- **import-linter** keeps the domain free of the application, infrastructure, and presentation layers, of SQLAlchemy, FastAPI, Starlette, and taskiq. It keeps the application free of the infrastructure and presentation layers and of the same frameworks, and the infrastructure free of the application and presentation layers. Only a presentation `dependencies` module imports the infrastructure. Each contract names the layers with `rastro.**.<layer>`, so it covers every app, `rastro.common`, and the test sample app.
- **ruff** bans FastAPI's and Starlette's `TestClient` through `TID251`, because a test runs on the app's event loop through `httpx.AsyncClient`.
- **pytest architecture tests** in `tests/architecture/` check the rules that import-linter cannot express:
  - Every domain module imports only the standard library, `pydantic`, and other domain modules of rastro, because import-linter has no allow list for the standard library.
  - No class of a domain module takes a `Protocol` in its constructor, so a domain object never holds a dependency.
  - No module outside a presentation package imports or reads FastAPI's `Depends`.
  - Every public function of an `application.use_cases` module is `async`, takes at most one positional argument, the Input, and takes every dependency as a keyword-only argument with no default.
  - Every error class of an `errors` module has a row in an error-to-status table, and the failure names each class that has none. `BaseError` rejects a missing code, a declared status, and a repeated code, and every code has the `<prefix>.<name>` form.
  - Every mapped class subclasses `Row`, and its table name starts with its app label.
  - Only `rastro.common.presentation.problems` imports `pydantic.ValidationError` or `pydantic_core`, or reads `ValidationError` from the `pydantic` module under any alias, because import-linter cannot name a member or a submodule of an external package. Test modules are exempt from this check, so a value object test can expect `pydantic.ValidationError`.
  - The extensions of `Problem` and `ValidationItem` follow their rules, and no class is named `BaseModel`.
