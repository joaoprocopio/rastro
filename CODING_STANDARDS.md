# Coding standards

These rules define how rastro code is structured. Other projects copy rastro's patterns, so every change follows these rules, and a change that breaks a rule on purpose updates this file in the same commit.

Use the domain terms from `GLOSSARY.md` in code, tests, and docs.

## Validate at the edge, trust the core

An edge is any place where data enters the system from outside the process. The database is an edge, and so is the network. The edges in rastro are:

- a view, which parses the HTTP request;
- a model field, which parses the values that the database returns and the values that the admin submits;
- a model manager that Django calls, for example `create_superuser` for `createsuperuser`;
- a client for an external service, which parses the response;
- a Celery task and a management command, which parse their arguments.

Each edge parses its raw input into value objects once. Services and selectors accept only value objects and other validated types, never raw `str` or `dict` input, so they hold business rules only.

Three levels split the work:

- **Validation** checks the shape of one value in isolation, for example "this is an email" or "the name has at most 320 characters". It lives in a value object in `<app>/values.py`, and nowhere else.
- **Business rules** depend on the state of the system, for example "the email is not in use" or "the Credentials are correct". They live in services and selectors.
- **Database constraints** (`unique`, `CheckConstraint`) are the last safety net. They never replace the two levels above.

These rules follow from the split:

- rastro code never calls `full_clean()`, `clean_fields()`, `validate_unique()`, or `validate_constraints()`, and models define no `clean()`. The admin still calls `full_clean()` through its ModelForm, so the fields in `rastro.common.fields` turn a failed value object into Django's `ValidationError` for the admin to show.
- A `CheckConstraint` violation means that an edge let invalid data through. It is a bug, so it responds with `500`.
- A `unique` violation is a business rule. The service checks for the conflict, catches the `IntegrityError` that a concurrent write can still cause, and raises a named `BaseError` subclass for both cases.
- Every edge validates, the database included. A value that the database returns and that fails its value object raises an error. No code path skips validation for a source that it trusts.

## Write value objects

A value object is a frozen Pydantic `RootModel` in `<app>/values.py` that subclasses `ValueObject` from `rastro.common.values`, and code reads its value through `.root`. Each value object declares its rules with `Annotated` and `StringConstraints`, so one line holds one rule:

```python
class DisplayName(
    ValueObject[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=320)]
    ]
):
    pass
```

A rule that `StringConstraints` cannot express, for example NFKC normalization, is a `BeforeValidator` that only transforms the value and never raises, so every rejection keeps the code of the rule that failed. Put the `BeforeValidator` before `StringConstraints` in `Annotated`. In the other order, Pydantic checks `pattern` before it applies `to_lower`, so `Email` would reject `Ana@x.com`.

An edge parses a raw value with `<ValueObject>.model_validate(value)`, which accepts a raw string or a built value object, and a schema field typed with a value object parses its JSON with no adapter code. Each value object is its own class, so mypy rejects a raw `str` or another value object in a service argument.

An enum is a `StrEnum` in `<app>/values.py`. Django's `TextChoices` stays out of the core.

A `values.py` module imports only the standard library, `pydantic`, and `rastro.common.values`, never Django. The fields in `rastro.common.fields` connect value objects to Django. `ValueObjectField` converts a model field to and from database values, and `ValueObjectFormField` parses a form input, for example the password of the admin add form. Both raise Django's `ValidationError` with the code of each field error, so the admin shows the error on its field. A model manager that Django calls parses inside `django_validation_errors()` from the same module, so `createsuperuser` prints the code. A value that the database returns and that fails its value object raises `pydantic.ValidationError`, so a request that reads it answers `500`.

## The frontend never validates

The frontend sends what the person typed and shows the errors that the backend returns. It runs no validation of its own, not even "required" or "minimum length", so each rule has one implementation. Every validation error from the backend points at its field and carries a stable problem type, so the frontend can show its own message next to the right input.

## Lay out an app

Each Django app is one context. An app uses a flat layout, with one module per role:

```text
<app>/
  models.py      # data and database constraints
  values.py      # value objects: the validation rules
  errors.py      # the BaseError subclasses of the app
  services.py    # commands: functions that write
  selectors.py   # queries: functions that read
  ports.py       # the Protocol of each dependency that the app uses
  adapters.py    # the implementations of the ports
  deps.py        # the real implementation chosen for each port
  schemas.py     # the Pydantic Input and Output of each operation
  views.py       # one view function per operation
  urls.py        # one named URL per view, under the app_name namespace
  admin.py
  tests/
    conftest.py  # the fixtures that more than one test of the app uses
    factories.py
    fakes.py     # one fake per port
    services/test_<service>.py
    selectors/test_<selector>.py
    views/test_<view>.py
```

When a module grows too large to read in one pass, it becomes a package with one module per entity, for example `services/identity.py` and `services/session.py`. The package `__init__.py` re-exports the public names.

Code that more than one app uses lives in `rastro/common/`. The `rastro` package itself holds only the Django project wiring: `settings/`, `urls.py`, `wsgi.py`, `asgi.py`, and `telemetry.py`.

## Write services and selectors

A service writes and a selector reads. Business logic lives in services and selectors only: views, schemas, models, managers, and signals hold none. Each function follows these rules:

- The name is `<entity>_<action>`, for example `identity_register`, `session_start`, or `identity_get_current`.
- Arguments are keyword-only and fully typed.
- A service that writes has `@transaction.atomic`.
- A service is a command. It returns `None`, never data and never an id. Only selectors return data.
- One service does one thing. For example, `identity_register` creates an Identity and does not start a Session.
- A model manager is an edge. It holds only the methods that Django requires, for example `create_user` and `create_superuser`, and each one parses its input into value objects and calls a service.
- A command is idempotent when the operation allows it. For example, ending a Session that does not exist still succeeds.

## Inject dependencies explicitly

A dependency is anything whose implementation you can swap without a change to the business rule, and every dependency is explicit. The dependencies in rastro include credential checks, the Session store, password hashing, email, file storage, the cache, the clock, id generation, cryptographic keys, task enqueueing, and every external API.

Two things are not dependencies:

- **The Django ORM and transactions** are the framework that the core couples to, as ADR 0001 records. Services and selectors use them directly.
- **Telemetry** uses the OpenTelemetry API, which already separates the API from the SDK. The observability plan decides its rules.

A port describes the business operation as it is today, not a provider that may come later. When a swap changes the flow, for example from Django authentication to an OpenID Connect provider such as Keycloak, the port changes with it, and an ADR records the change.

Each app declares the ports it consumes in `ports.py` and implements them in `adapters.py`. An adapter that several apps use, for example an SMTP mailer, lives in `rastro/common/adapters/`, and each consumer app still declares its own port. Only adapters read `django.conf.settings`. A service that needs a configuration value receives it through a port.

A service or selector receives each dependency as a required keyword-only argument, typed with a `typing.Protocol`. A dependency argument has no default, so every caller passes every dependency and mypy rejects a call that leaves one out. When a service calls another service, it passes the dependencies down by name.

A `Protocol` works like a Rust trait: an implementation never inherits from it, and the code uses no `abc.ABC`. Below each real implementation, one line asks mypy to check that it matches its protocol. The line is named after the port, because a module that holds two adapters cannot assign `_` twice without a `no-redef` error from mypy:

```python
_authenticator: Authenticator = django_authenticate
```

Only the services and selectors of a Session receive the `HttpRequest`, because Django keeps the Session in the request. Every other service and selector runs without a request, so a Celery task or the shell can call it.

Each app has a `deps.py` that holds one constant per real implementation, for example `AUTHENTICATE: Authenticator = django_authenticate`. It holds no factories, containers, or logic. Each edge imports `deps.py` and passes the constants by name, and a test passes a fake in their place.

A long parameter list is acceptable. Dependencies are never grouped into a bundle object, so the signature of each service shows every dependency it uses.

## Write views

A view is a Django view function in `<app>/views.py` that handles one operation, named `<entity>_<action>_view`, for example `session_start_view`. Each view has its own URL. A command uses `POST` on a URL that names the action, for example `POST /api/v1/iam/session/start`, and a query uses `GET`, for example `GET /api/v1/iam/session`. The decorators `require_POST` and `require_GET` from `rastro.common.views` restrict the method and raise `MethodNotAllowedError` for any other method, which the exception middleware answers with a problem details `405`. The view parses the input with `parse_body`, calls one service or one selector, and builds the response with `respond`, both from `rastro.common.views`. It holds no business logic, and no view is exempt from CSRF.

Each app's `urls.py` sets `app_name` to the app label, and each URL pattern has a name: the view name without `_view`, for example `name="session_start"`. Code and tests build a URL with `reverse("iam:session_start")` and never type the path. The Django hooks in `rastro.common.views` follow the same rule: `csrf_failure_view`, `not_found_view`, and `server_error_view`.

The request and response schemas live in `<app>/schemas.py` and are named `<Entity><Action>Input` and `<Entity><Action>Output`, for example `SessionStartInput`. Each schema belongs to one operation, and no other operation reuses it, so an operation can change its format without breaking another one. Only `views.py` imports `schemas.py`.

An Output schema sets `model_config = pydantic.ConfigDict(from_attributes=True)`, and the view builds it with `SessionCurrentOutput.model_validate(identity)`, so a new output field is one line in the schema. A field that reads another attribute declares `Field(validation_alias=...)`, with an `AliasPath` for a related model, because `alias` also renames the JSON member. A computed value comes ready from the selector, for example as a queryset annotation, so the schema holds no logic.

A command view responds with no body: `201` when it creates something and `204` otherwise. A query view responds with its `Output` schema.

## Return errors as problem details

Every error response uses RFC 9457 (`application/problem+json`) and carries only `type` and `status`. The `type` is `/problems/<code>`, and it is the identifier that a client reads: a frontend picks its own text from it, and an API consumer can look it up. The response carries no `title`, `detail`, or `code` member, and it omits a member that has no value. Every error has a code, so a `404`, a `405`, and a `500` carry a `type` too.

### Declare an error as a class

An error is a class that declares its code and its HTTP status, so one class holds everything about one error, and a new error needs this class and nothing else. Each app declares its errors in `<app>/errors.py` as subclasses of `BaseError` from `rastro.common.errors`, and each class name ends in `Error`:

```python
class EmailInUseError(BaseError):
    code = "iam.email_in_use"
    status = HTTPStatus.CONFLICT
```

A code has the form `<prefix>.<name>`. The prefix is the app label for the errors of an app, `request` for the errors of an HTTP request that every app shares, and `server` for a failure of rastro itself. The status costs nothing outside HTTP: a Celery task ignores it.

`BaseError` checks each subclass when Python creates it. It raises `TypeError` when the subclass declares no `code` or no `status`, and when another class already declares the same code, and the message names both classes. A repeated code therefore fails at import time. An architecture test imports every app's `errors` module, so the check runs for every app, and it checks the `<prefix>.<name>` form.

An error that holds data takes it in its constructor. `ValidationFailedError` holds one `ValidationItem` per failed field, with its JSON Pointer and its field error. `TooShortError` holds `min_length`, `TooLongError` holds `max_length`, and `MethodNotAllowedError` holds the method that the URL allows.

### Translate errors in the problems module

The problems module, `rastro.common.problems`, is the only translation layer in rastro. No other module builds a problem body or reads a Pydantic error type. The problems module exports four public names, and every other name in it starts with `_`:

- `validation_failed_errors()` is a context manager that turns a `pydantic.ValidationError` raised inside it into a `ValidationFailedError`.
- `to_error(exception)` returns a `BaseError` unchanged, turns an `Http404` into a `NotFoundError`, and returns `None` for any other exception, a `pydantic.ValidationError` included.
- `Problem.from_error(error)` builds the body of a `BaseError`.
- `problem_response(problem)` returns an `HttpResponse` with the body, the status, and the media type, and it sets `Allow` for a `MethodNotAllowedError`.

Only a parse inside `validation_failed_errors()` answers `422`. A `pydantic.ValidationError` raised outside it, for example by a corrupted value that the database returns, reaches `to_error` unchanged and answers `500`.

Every other module calls these names in place of a translation of its own:

- `parse_body` parses inside `validation_failed_errors()`, so a request body that fails its schema answers `422`.
- The exception middleware passes each exception through `to_error`. It answers the problem of the error, and it lets Django handle the exception when `to_error` returns `None`. It imports nothing from Pydantic.
- `require_POST` and `require_GET` raise `MethodNotAllowedError`, and the middleware answers it like any other error.
- `csrf_failure_view` answers `CsrfFailedError`.
- `not_found_view` passes its exception through `to_error`, so a `404` from the URL resolver and an `Http404` from a view answer the same problem.
- `server_error_view` answers `InternalServerError`. An unhandled exception reaches it, a `CheckConstraint` violation included.
- `django_validation_errors()` wraps `validation_failed_errors()` and raises Django's `ValidationError` with the code of each item. `ValueObjectField`, `ValueObjectFormField`, and the model managers parse inside it.

### Report a validation failure per field

A validation error responds with `422`, the type `/problems/request.validation_failed`, and an `errors` extension with one item per field. Each item has a JSON Pointer to the field and the problem type of the rule that failed, never of the value object, so a frontend can tell "too long" from "wrong format" on the same field. A length item also carries its limit, so the frontend can show "at least 8 characters" with no copy of the rule:

```json
{
  "type": "/problems/request.validation_failed",
  "status": 422,
  "errors": [
    {"pointer": "#/email", "type": "/problems/request.invalid_format"},
    {"pointer": "#/password", "type": "/problems/request.too_short", "min_length": 8}
  ]
}
```

The problems module translates each Pydantic error type to a rastro error, so the contract never exposes Pydantic's vocabulary:

- `missing` becomes `FieldRequiredError`.
- `json_invalid` becomes `InvalidJsonError`.
- `extra_forbidden` becomes `UnknownFieldError`.
- `string_too_short` and `too_short` become `TooShortError`, and the item carries `min_length`.
- `string_too_long` and `too_long` become `TooLongError`, and the item carries `max_length`. Pydantic reports `too_long` when the length rule runs after a `BeforeValidator`, as in `Email`.
- `string_pattern_mismatch` becomes `InvalidFormatError`. The item omits the pattern, so no client copies the regular expression.
- Any other type becomes `InvalidTypeError`.

## Test by layer

Value object tests are pure and use no database. They check the normalization of each value object and that a bad value raises `pydantic.ValidationError`, and the view tests own the code of each rejection. Service and selector tests cover the business rules, use the test database, and pass a fake for each port, so no test uses `mock.patch`. A service test asserts the error class with `pytest.raises`. View tests cover the HTTP contract: status codes, bodies, headers, and cookies. A view test compares the literal JSON of each problem, because the literal is the contract that a client reads.

Before you write a test, look in the app's `tests/conftest.py` for a fixture that builds the state the test needs, and ask for it by name. When a second test needs the same state, add a fixture to that `conftest.py`, and keep the test file free of setup helpers. A fixture that more than one app uses lives in the root `conftest.py`. A test outside an app, for example the telemetry test in `rastro/tests/`, cannot see the fixtures of the app, so it calls the factory of the app and `force_login` in the test. A `pytest_plugins` line in the root `conftest.py` would give it the fixtures, but it makes every fixture of the app global. A test that needs a variation of the shared state, for example a second Identity, calls the factory_boy factory from `tests/factories.py` in the test, so the fixture set stays small.

A test that needs a Session starts it with `force_login`, for example through the `signed_in_client` fixture of `iam`. A test posts Credentials to the `session_start` view only when the start itself is the behaviour under test, for example a wrong password or an email that registration normalized.

A test builds each URL with `reverse()` and posts JSON with the Django test client, `client.post(url, payload, content_type="application/json")`, which encodes the payload. Test classes are optional, so group tests in a class only when the group helps the reader.

## Check the architecture

Tools check these rules, and every change passes them before it merges, so a violation fails the check instead of waiting for a review:

- **import-linter** checks the layers: `views` imports `schemas`, `services`, and `selectors`, which import `models` and `values`, and no module imports a layer above it. Only `views` imports `schemas`. `services` and `selectors` never import `pydantic`, and `values` never imports Django. import-linter cannot name `django.conf`, because it squashes an external package to its top-level name, so the pytest architecture tests check that `services` and `selectors` never import `django.conf`. `services` and `selectors` import `ports` but never `adapters`, and only `deps.py` imports `adapters`.
- **ruff** bans `django.dispatch.receiver` and `django.views.decorators.csrf.csrf_exempt` through `TID251`, because signals hold no business logic and no view is exempt from CSRF.
- **pytest architecture tests** in `tests/architecture/` inspect every public function in `services.py` and `selectors.py`. Each argument is keyword-only and typed, no argument is a raw `str` or `dict` except the `request` of a Session, no dependency argument has a default, every service returns `None`, and every name follows `<entity>_<action>`. The same tests check that no code calls `full_clean()` or its siblings, and that `values.py` imports only the standard library, `pydantic`, and `rastro.common.values`, because import-linter has no allow list for the standard library. Only `rastro.common.problems` imports `pydantic.ValidationError` or `pydantic_core`, or reads `ValidationError` from the `pydantic` module under any alias, because import-linter cannot name a member or a submodule of an external package. Test modules are exempt from this check, so a value object test can expect `pydantic.ValidationError`. They also walk the root URLconf: every URL whose view lives in `rastro` has a name inside an app namespace, and every view, the error handlers and the CSRF failure view included, is a `<entity>_<action>_view` function in a `views` module. Every `*Output` schema sets `from_attributes`, and no `views` module calls an `*Output` class, so a view builds its Output only with `model_validate`.

## Configure settings

Settings live in `rastro/settings/`. `base.py` holds every setting, `test.py` overrides values for the test run, and each integration has its own module, for example `telemetry.py`. No setting exists only in production: environment variables, read with `get_env`, switch features on and off. Every environment variable has the `RASTRO_` prefix, for example `RASTRO_SECRET_KEY`.
