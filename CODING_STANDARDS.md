# Coding standards

These rules define how rastro code is structured, and they hold only what the code cannot say: the conventions that a new module follows, and the reasons behind them. Other projects copy rastro's patterns, so a change that breaks a rule on purpose updates this file in the same commit.

Use the domain terms from `GLOSSARY.md` in code, tests, and docs. The architecture decision record (ADR) 0001 records why rastro uses FastAPI, SQLAlchemy 2, and taskiq in four layers. The test sample app in `rastro/common/tests/sample/` is the reference for the four layers, so read it before you add an app.

## Validate at the edge, trust the core

An edge is any place where data enters the process. The edges in rastro are:

- a view, which parses the HTTP request
- a mapper from a row to an aggregate, which parses each value object of the row
- a task, which parses its arguments
- a client of an external service, which parses the response

Each edge parses its raw input into value objects once, so a use case accepts only value objects and data transfer objects (DTOs), never a raw `str` or `dict`. The database is an edge too, so a row that fails its value object raises when the mapper builds the aggregate. No code path skips validation for a source that it trusts.

Three levels split the work:

- **Validation** checks one value in isolation, for example "this is an email". It lives only in a value object.
- **Business rules** depend on the state of the system or on several fields. A rule that reads only the fields of one aggregate is a method of the aggregate. A rule that needs other data lives in a use case.
- **Database constraints** are the last safety net, and they never replace the two levels above.

The split decides the status of a database error. A `CheckConstraint` violation means that an edge let invalid data through, so it is a bug that answers `500`. A `unique` violation is a business rule. The use case checks for the conflict, and the repository's `add` and `update` translate the `IntegrityError` of a concurrent write into the `BaseError` subclass of that rule, for example `EmailInUseError`. The repository translates only a `psycopg.errors.UniqueViolation` on the constraint of that rule, so any other `IntegrityError` still answers `500`.

## Raise in place of a fallback value

Application code holds no fallback for a state that it does not expect: no `or ""`, no `.get(key, {})`, and no `getattr(obj, name, None)` for an attribute that must exist. The code raises, so the error reaches the observability platform as a `500`. A default stays only where the absence is a valid state, for example an optional DTO field or a setting.

A broken invariant raises a built-in exception whose message names the value, for example `LookupError(f"No User with the id {id.root}.")`. It never raises a `BaseError`, because a `BaseError` is a rule that a client can break. Application code narrows a type with `if ... is None: raise`, never with `assert`, because `python -O` removes an `assert`. A test narrows with `assert`.

## Lay out an app in four layers

Each app is one bounded context, and its package name is its app label, for example `auth`. An app has four layer packages with fixed module names, so a reader finds a concept at the same place in any app:

```text
<app>/
  domain/
    aggregates.py      # data with the rules that read only its own fields
    value_objects.py   # the validation rules
    errors.py          # the BaseError subclasses of the app
    ports.py           # the Protocol of each repository and dependency
  application/
    use_cases.py       # one async function per operation
    dtos.py            # the Input and Output of each use case
    mappers.py         # aggregate to Output DTO
  infrastructure/
    models.py          # rows
    mappers.py         # row to aggregate, and aggregate to row
    repositories.py    # one repository per aggregate
    adapters.py        # the other implementations of the ports
  presentation/
    dependencies.py    # the FastAPI dependency that builds each adapter
    views.py           # the router, the views, and the error-to-status table
    tasks.py           # the taskiq tasks
  tests/
```

An app creates a module when the module gets its first member. A module that grows too large to read in one pass becomes a package with one module per aggregate, and its `__init__.py` re-exports the public names.

Only the presentation's `dependencies` module imports the infrastructure, to build adapters. `rastro/common/` holds the code that more than one app uses, in the same four layers, and the `rastro` package itself holds only the wiring.

## Choose the form of code

Every piece of code takes one of four forms, so a reader can tell what the code does from its kind:

- **Data** is a class: an aggregate, a value object, a DTO, an error, a row, or an enum. It receives no dependency, and its methods read only its own fields and their arguments. A `typing.NamedTuple` is data only as the result of a domain method that holds several values and no rule, such as `PasswordCheck`. No edge parses it, so it needs no Pydantic validation.
- **A port** is a `typing.Protocol` in the domain's `ports` module, for each dependency that the core swaps between production and tests, such as a repository, a hasher, or a clock.
- **An adapter** implements a port and receives its configuration or resource once, in its constructor.
- **Everything else is a function**: a use case, a mapper, a view, a FastAPI dependency, and a task.

An adapter takes the name of its technology and its port, for example `SqlUserRepository` or `SystemClock`, and keeps its state in private attributes. A fake is named `Fake<Port>`, lives in the app's tests package, and keeps its state in public attributes, so a test reads what the use case wrote.

An adapter does not inherit its `Protocol`, and the code uses no `abc.ABC`, so a fake and a real adapter have the same standing. mypy checks conformance where a dependency function returns the adapter as the port type. A class inherits only from a framework base or from a rastro base that carries configuration or declaration rules, such as `Aggregate` or `Row`.

A construction that follows a rule is a classmethod named after the act, with keyword arguments only, for example `Session.start(...)` or `SessionToken.generate(nbytes=...)`, so no caller repeats the rule. Every function or method takes its subject as its one positional argument and every other argument by keyword, so a call reads without the signature: `hasher.verify(password=..., hashed=...)`. A function with no subject takes only keywords. A domain method that receives the time names the argument `at`.

A data type is always a class, never a module-level `Annotated` or `Literal` alias, because mypy cannot tell two aliases of one type apart. A constraint goes inside the class, and a fixed set of texts is a `StrEnum`. Two aliases stay. A FastAPI dependency alias stays, because FastAPI reads `Depends` only inside `Annotated`. A `type` statement that names the shape of a container stays, because it holds no value that mypy must tell apart.

## Write Pydantic classes

Every Pydantic class subclasses the rastro base of its kind (`Aggregate`, `ValueObject`, `RootValueObject`, or `DTO`) and inherits one strict configuration. No class is named `BaseModel`, so `BaseModel` always means Pydantic's class. Two flags of that configuration carry a reason. `extra="forbid"` rejects an unknown key, so a misspelled optional field fails in place of a silent drop. `hide_input_in_errors` keeps the input out of a `ValidationError` message, so a password or an email never reaches a log.

An aggregate method exists only when a change protects a rule across fields. Otherwise a use case assigns the field, and `validate_assignment` checks the value. An aggregate refers to another aggregate only by its `Id`, so a repository loads and writes one aggregate at a time.

FastAPI validates the Python result of the parsed JSON, so `strict` rejects a JSON string for a field whose Python type is not `str`, such as a `StrEnum`, a `datetime`, or a `UUID`. Such a DTO field declares `Field(strict=False)`. A value object that `Settings` parses from an environment variable declares the same on its root.

## Write value objects

A value object declares each rule with `Annotated` and `StringConstraints`, so one line holds one rule. A rule that `StringConstraints` cannot express, for example NFKC normalization, is a `BeforeValidator` that only transforms and never raises, so every rejection keeps the code of its rule. The `BeforeValidator` goes before `StringConstraints`, because Pydantic checks `pattern` before it applies `to_lower`, and `Email` would then reject `Ana@x.com`.

A limit that a row column repeats is a module-level constant in `value_objects`, for example `EMAIL_MAX_LENGTH`, so the rule and the column change in one place.

Every aggregate id is an `Id`, so all ids share one type, and a row with the id `0` fails when it becomes an aggregate. A future id kind that Python generates, for example a ULID, gets its own value object beside `Id`.

A configuration value with a rule is a value object too, for example `TokenBytes`, so an invalid value fails wherever code builds it. The settings, the use case, and the aggregate pass the value object, and only the code that needs the number reads `.root`.

A value object that holds a secret wraps a `SecretStr`, so a log line or a traceback shows `**********`. A secret is a value that lets its holder act, such as a password or a token. A digest stays plain, because it lets no one act, and so does a value that a response sends, such as `Email`. Code reads a secret with `.root.get_secret_value()` only where it hashes the secret, writes a cookie, or compares two tokens, and a test reads it to check the value. A Session stores only the digest of its Session token, so a leaked database starts no Session.

A token value object has no format rule. A header or a cookie then always parses, and a wrong token fails the check that compares it, in place of a validation error. `CsrfToken` lives with the rest of CSRF in `rastro.common.presentation.csrf`, and its `matches` compares UTF-8 bytes, because `secrets.compare_digest` raises `TypeError` on a `str` with characters outside ASCII, so such a header answers `403` and not `500`.

A value object equals only a value object of its own class, so `Id(1) == 1` is false.

## Validate only in the backend

The frontend sends what the person typed and shows the errors that the backend returns. It runs no validation of its own, not even "required", so each rule has one implementation. Every validation error points at its field and carries a stable problem type, so the frontend shows its own message next to the right input.

## Write use cases

A use case is an `async def` named `<entity>_<action>`, for example `user_register`, and it follows these rules:

- It takes the Input DTO as its first argument, when the operation has one. It takes every port after the Input as a required keyword-only argument, so mypy finds every caller that a new dependency affects. It never groups dependencies into a bundle object, so the signature shows every dependency.
- It takes each configuration value after the ports, as a keyword-only argument with the type of its setting. The view reads the value from the settings, so the application and the domain never read `Settings`.
- It returns an Output DTO, a value object, or nothing.
- It reads the time from the `Clock` port and passes it to the domain as a value, so a domain test needs no fake clock.
- It creates a random secret with the `generate` method of its value object and returns the secret. A port wraps only a source that a test must control, and a test reads a random value from the return value.
- It never calls `commit` or `rollback`, because the edge owns the transaction.
- It reads through a repository that returns an aggregate, so a read has the same shape as a write.

A step that several use cases share is a function of the same module whose name starts with `_`, and a test reaches it only through the public use cases.

An operation is one chain of plain function calls from the view or task to the repository. rastro has no read model, no domain event, and no command bus.

A port describes the business operation as it is today, not a provider that may come later. When a swap changes the flow, for example from a password check to OpenID Connect, the port changes with it, and an ADR records the change.

## Declare rows and repositories

A row subclasses `Row`, takes the suffix `Row`, and has `Mapped` columns of primitive types. Its table is named `<app label>_<entity>`, for example `auth_user`. The prefix also avoids reserved words, because `select * from user` in Postgres returns the database user with no error. The column conventions follow:

- `id` is `bigint generated by default as identity`. A foreign key references the column object, for example `ForeignKey(UserRow.id)`, so a rename fails mypy, and it declares `index=True`.
- `created_at` and `updated_at` use `server_default=func.now()`, and `updated_at` also uses `onupdate`, so no Python code reads a clock for audit data.
- A unique constraint that a repository translates has an explicit name in `__table_args__`, so the repository and the migration read one name.

A repository is one adapter per aggregate, and it receives the `AsyncSession` in its constructor, so the application never imports SQLAlchemy. Its methods follow these rules:

- `next_id` takes the id from the column's sequence, so every aggregate has its id from its creation. A rolled-back transaction leaves a gap.
- `add` and `update` flush, so a constraint violation rises inside the method, where the repository translates it.
- `update` and `remove` load the row through `existing_row`, which raises `LookupError` for a missing id, because `merge` alone would insert a missing row.
- A mapper sets no audit column, so `merge` keeps `created_at`.
- A `get_by_*` method returns the aggregate or `None`.

A fake repository passes the behaviour suite of its port, so a use case test that passes with the fake also passes on Postgres. It stores and returns a `model_copy()` of each aggregate, so a use case that assigns a field without `update` leaves the stored aggregate as it was. Its `add` and `update` raise the error of each unique rule, and its `update` and `remove` raise `LookupError` for a missing id.

## Map between layers by hand

Each conversion between layers is a function that names every field, so mypy checks each field. A row, an aggregate, and a DTO use the same field names, so a mapper reads as a list of equal pairs. A different name, or a value object that spans several columns, gets its conversion in the same mapper. A mapper from a row calls `model_validate` on each value object.

An infrastructure mapper names its direction, for example `note_from_row` and `note_to_row`. An application mapper has one direction, so it takes the name of its Output DTO in snake case, for example `session_get_output`.

## Migrate with Alembic

Create a migration with `uv run --env-file .env.example alembic revision --autogenerate -m "<what changes>"`, and read it before you commit it. The message names the change and the table, for example `create auth_user`.

## Build adapters in the presentation dependencies

Each route declares every adapter as an `Annotated[Port, Depends(factory)]` parameter, so its signature shows every dependency, and a test swaps the factory through `app.dependency_overrides`. A task calls the same factories with the session of its own transaction.

A factory builds a new adapter on each call. An adapter that is costly to build and holds no request state is the exception, so its factory is `@functools.cache`, for example `password_hasher`. A factory that does no I/O is a plain `def`.

An adapter that several apps use lives in `rastro.common.infrastructure.adapters`, and each consumer app still declares its own port. In an app, only adapters, dependencies, and views read `Settings`.

## Write views

A view is an `async def` named `<entity>_<action>_view`. It reads typed parameters, calls one use case, and returns its Output DTO or nothing, with no business logic. It never calls the body of a task, and it sends a task with `<task>.kiq(...)`. A view that only hands the client a value of the edge calls no use case, because no business rule and no row is involved. `csrf_set_view` is the one such view.

Each app has one `APIRouter` under `/api/v1/<app label>/`, and each router declares `dependencies=[Depends(csrf_check)]`, so a new app cannot forget the CSRF check. The module `rastro.common.presentation.csrf` holds all of CSRF, and its own router serves `GET /api/v1/csrf`, so no app depends on another app for the CSRF cookie. A command uses `POST` on a path that names the action, for example `POST /api/v1/auth/session/start`, and a query uses `GET`.

A views module holds its parts in this order: `ERROR_STATUSES`, the `router`, the private request dependencies, and the views. It calls `use_cases.<name>` through the module, so a parameter such as `clock` never hides a function of the same name.

The request transaction depends on `scope="function"` in the `DatabaseSession` alias. With FastAPI's default scope, the dependency exits after the response, so a failed commit would follow a `2xx` response.

Each operation has its own `<Entity><Action>Input` and `<Entity><Action>Output`, and no other operation reuses them, so an operation changes its format without breaking another one. FastAPI reads them as the request body and the response model, so the presentation needs no mapper. An application DTO holds no field that only one edge uses. When an edge needs a shape that differs from the application DTO, that edge adds its own presentation DTO.

A command responds with no body: `201` when it creates something and `204` otherwise. FastAPI drops the body of a `204` only, so a `201` view declares `response_class=Response`, or FastAPI sends `null`. A view never calls `set_cookie` or `delete_cookie` itself, and passes its `response` to the module that owns the cookie, so the name and flags of a cookie live in one place.

A value outside the body, for example a cookie, comes from a private dependency function with an alias, which returns a value object or `None`. A cookie dependency sits in the module that owns the cookie. It never declares a `Cookie`, `Query`, or `Header` parameter with a rule, because such a parameter that fails validation answers `500`. The value object has no rule, and the use case answers a bad value with its own error.

## Write tasks

A task is an `async def` named `<entity>_<action>_task`, and it is an edge. It parses its arguments, opens its own transaction, builds its repositories with the `dependencies` factories, and calls one use case. It never uses FastAPI's `Depends`.

The task opens the transaction in its body with `sessionmaker.begin()`, not in a `yield` dependency, because taskiq closes a dependency after it records the result, so a failed commit would follow a successful task. A task declares itself on `async_shared_broker`, so a tasks module imports no broker, and a change of broker changes only `rastro/broker.py`.

The ZeroMQ broker needs no server, and it has these limits:

- With N workers, each task runs N times, so the stack runs one worker.
- A task sent while the worker is down is lost.
- No result backend exists, so a caller cannot read the result of a task.
- The API binds the publish address, so the API runs in one process.

## Trace without personal data

Each process entry calls `instrument` before the other instrumentations, because each instrumentation reads the global provider. `create_app`, `create_database_engine`, and `create_broker` stay free of telemetry, so a test builds them with no exporter. Application code uses only the OpenTelemetry API, never the SDK, and the API already separates the code from its exporter, so telemetry is not a port.

A span never holds personal data. The FastAPI span keeps the URL with its query string, so personal data never goes into a query string.

The collector starts before the API and the worker. When the exporter flushes at exit with no collector, it retries past the 10 seconds that `docker compose stop` waits, and Docker kills the process with exit code 137.

## Return errors as problem details

Every error response is an RFC 9457 problem with `application/problem+json`. Its `type` is the error code, for example `auth.email_in_use`, and a client picks its own text from it. Every problem carries `type` and `status`, a `404`, a `405`, and a `500` included.

An error is a `BaseError` subclass in the domain's `errors` module, its name ends in `Error`, and it declares `code = "<prefix>.<name>"`. The prefix is the app label, `request` for an HTTP error that every app shares, or `server` for a failure of rastro itself. An error carries no HTTP status, so a task raises the same error as a view. An error with data declares its own extensions class, which is a `ValueObject` for a domain error and a `DTO` for a request error.

The presentation layer chooses each status. Each app's `views` module declares an `ERROR_STATUSES` table, and `rastro/app.py` merges the tables. A new error therefore needs its class and a row in its app's table, and a new app needs its table in the merge. The handlers read the exact class, so a subclass needs its own row.

`rastro.common.presentation.problems` is the only module that builds a problem body or reads a Pydantic error type. A new validation rule with data needs an error class with its extensions and one case in its `match`. No problem shows the input value, so `InvalidFormatError` has no extensions, and the pattern of a rule never reaches a response.

## Configure settings

A setting holds every value that an operator may change, for example a cookie name, a cookie flag, or a token size. A value that a standard fixes stays a constant, for example `SAFE_METHODS`. Every setting has a default except `RASTRO_POSTGRES_URL`, so no password sits in the code. A password with `@` or `/` needs percent-encoding in that URL. `RASTRO_OPENAPI_ENABLED` is off by default, so a deployment that forgets the variable shows no route list.

A new setting needs a field with a default and a line in `.env.example`. Only a process entry and a test build `Settings()`, and every factory receives the settings as an argument, so a test builds each one with the settings of its own database. An HTTP test changes a setting through `app.dependency_overrides[app_settings]`.

## Write Python for mypy strict

Every function has full annotations, a test and a fixture included. The code uses Python 3.15 syntax:

- A generic declares its type parameter in place, as in `class RootSchema[T]`, with no `TypeVar`.
- A union is `X | None`.
- An abstract container type comes from `collections.abc`.
- An import is absolute, from `rastro.`.
- An HTTP status is an `HTTPStatus` member, never a number.

## Test by layer

Each layer has its own kind of test. A test passes fakes as arguments or through `app.dependency_overrides`, so no test uses `mock.patch`, and only a settings test uses `monkeypatch`, for environment variables. The kinds of test are:

- **Domain tests** are pure, with no database and no fake. They check each value object, with no input in the message of the `ValidationError`, and each aggregate method.
- **Use case tests** call a use case with the in-memory fakes and assert the error class with `pytest.raises`.
- **Repository tests** run one behaviour suite per port, and its `adapter` fixture runs each test once with the fake and once with the Sql adapter. Only the Sql case opens the test database, and it reads back through a second session, so the identity map hides nothing. The suite covers both mapper directions, `next_id` and the `Id` that it returns, the unique-violation translation, `LookupError` for a missing row, and the `model_copy()` rule. A test that only Postgres can pass lives in `test_sql_<aggregate>_repository.py`: a row that breaks its value object, such as the id `0`, the audit columns, and the query span.
- **View tests** cover the HTTP contract and compare the literal JSON of each problem, because the literal is the contract that a client reads. The view tests own the code of each rejection.
- **Task tests** send the task through taskiq's in-memory broker and read its rows.

A test lives in `rastro/<app>/tests/`, beside the code that it covers, for example `views/test_session_start.py`. A test name states the behaviour as a sentence, for example `test_an_email_in_use_is_a_conflict`, and a blank line splits the setup and the call from the assertions. An input that several tests share is a module-level constant. A test class is optional, so group tests in a class only when the group helps the reader.

Before you write a test, look in the `conftest.py` files for a fixture that builds the state you need. When a second test needs the same state, add a fixture to the app's `conftest.py`, so the test files hold no setup helpers. A fixture that more than one app uses lives in the root `conftest.py`. A test that needs a variation of the shared state calls the factory in the test. A fixture whose state its name does not tell has a one-line docstring.

An error class that a test declares takes the prefix `tests`. A made-up domain in a test uses the painting vocabulary of the sample app: `paint`, `wall`, and `brush`. The sample rows have their own `MetaData`, so Alembic never migrates them.

## Check the architecture

import-linter, ruff, and the pytest tests in `tests/architecture/` check the rules that can fail mechanically, for example the layer imports, the use case signatures, and the error-to-status table. A violation then fails the check before a review.

Each architecture rule is a function in `tests/architecture/rules.py` that returns one `<module>:<line>: <source>` string per violation, so a failure names every place to fix. Its test asserts that the list is empty, and it feeds the rule a made-up source to assert each violation. A rule that discovers modules also asserts that it finds the modules of `auth` and of the sample app, so a broken rule cannot pass in silence.
