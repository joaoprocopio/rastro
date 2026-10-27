# Apply the maintainer's review of the layered architecture

Status: ready-for-agent

## Problem Statement

The maintainer reviewed the `layered-architecture` branch and left review comments in 16 modules. A grilling session settled each comment. The branch has these problems:

- A log line or a traceback that prints a `RawPassword`, a `SessionToken`, or the settings shows the password, the token, or the database password in clear text.
- Every id is a bare `int`, and `next_id` reads a hard-coded column name, so a renamed column fails only at runtime.
- Some names read badly. The mapper `user_get_current_output_from_user` repeats its argument type in its name, and `SessionTokenHash` breaks the pattern of `HashedPassword`.
- The cookie names, the cookie flags, the CSRF header name, the token sizes, and the Session lifetime are constants in the code. An operator who integrates a frontend must change the code to change them, where Django exposes each one as a setting.
- Every setting is required, so a local run needs all of them, even where a safe default exists.
- `RASTRO_POSTGRES_URL` accepts a `postgresql://` URL. The process then fails later with an error that does not name the variable.
- The Session repository sets the User's id on the current span. The maintainer does not want this telemetry now.
- A CSRF token is a bare `str`, while the Session token is a value object.

## Solution

rastro keeps its four layers and its HTTP contract. Secrets hide their values in `repr`. One `Id` value object types every id. The names follow the maintainer's choices. Every cookie value, the CSRF header name, the token sizes, and the Session lifetime become settings with Django-style names and today's values as defaults. Every setting except `RASTRO_POSTGRES_URL` has a default. The Session repository stops writing the User's id to the span. A `CsrfToken` value object replaces the bare CSRF string.

The JSON body of every route under `/api/v1/auth/` stays the same. The one new behaviour is that `RASTRO_OPENAPI_ENABLED` defaults to `false`.

## User Stories

### Maintainer of rastro

1. As a maintainer, I want `RawPassword` to hide its value in `repr`, so that a traceback or a log line never shows a password.
2. As a maintainer, I want `SessionToken` to hide its value in `repr`, so that a log line never shows a token that acts as a User.
3. As a maintainer, I want `CsrfToken` to hide its value in `repr`, so that every token value object behaves the same way.
4. As a maintainer, I want `Email` and `DisplayName` to stay plain strings, so that the response of `GET /session` still sends their values and not asterisks.
5. As a maintainer, I want `HashedSessionToken` to stay a plain value, because a SHA-256 digest starts no Session.
6. As a maintainer, I want the settings to hide the database password in `repr`, so that a log of the settings never shows it.
7. As a maintainer, I want one `Id` value object that holds a positive integer, so that every aggregate's id has one type.
8. As a maintainer, I want `Id` to reject `0` and negative numbers, so that a corrupted row fails when it becomes an aggregate.
9. As a maintainer, I want `User.id`, `Session.id`, `Session.user_id`, and `Note.id` to use `Id`, so that every id in the domain has the same type.
10. As a maintainer, I want `next_id` to receive the column object and return an `Id`, so that a renamed column fails mypy.
11. As a maintainer, I want `existing_row` to receive an `Id`, so that the repository passes the domain type without a conversion.
12. As a maintainer, I want a `LookupError` from a missing row to answer `500`, so that a bug or a race reaches the observability platform.
13. As a maintainer, I want the operation that reads the User of the current Session named `session_get`, so that its name follows its route, `GET /api/v1/auth/session`.
14. As a maintainer, I want its Output DTO named `SessionGetOutput` and its view named `session_get_view`, so that every name of the operation matches.
15. As a maintainer, I want each application mapper named after its Output DTO, for example `session_get_output(user)`, so that the name does not repeat the argument type that mypy already checks.
16. As a maintainer, I want `SessionTokenHash` renamed to `HashedSessionToken`, so that it follows `HashedPassword`.
17. As a maintainer, I want the Session field, the row column, and the repository lookup that hold the digest renamed to `hashed_token`, so that the row, the aggregate, and the value object use one name.
18. As a maintainer, I want `SessionToken.generate(nbytes=...)` to build a new Session token, so that one method creates every Session token.
19. As a maintainer, I want `CsrfToken.generate(nbytes=...)` to build a new CSRF token, so that both tokens follow one pattern.
20. As a maintainer, I want the Session repository to stop setting the User's id on the span, so that the repository holds no telemetry code.
21. As a maintainer, I want the request, query, and task spans to stay, so that the removal touches only the User's id.
22. As a maintainer, I want the review comments removed from the code, so that the code holds no question that this spec answers.
23. As a maintainer, I want the `lifespan` of the app annotated as an async generator, so that Pylance shows no deprecation warning.
24. As a maintainer, I want the domain to receive the Session lifetime as a value, so that a domain test passes a `timedelta` and needs no environment variable.

### Operator who deploys rastro

25. As an operator, I want to set the Session lifetime with `RASTRO_SESSION_LIFETIME`, so that I change it with no change to the code.
26. As an operator, I want to set the name of the Session cookie with `RASTRO_SESSION_COOKIE_NAME`, so that two rastro deployments on one domain keep separate cookies.
27. As an operator, I want to set the `Secure`, `HttpOnly`, and `SameSite` flags of the Session cookie with `RASTRO_SESSION_COOKIE_SECURE`, `RASTRO_SESSION_COOKIE_HTTPONLY`, and `RASTRO_SESSION_COOKIE_SAMESITE`, so that I fit the cookie to my frontend.
28. As an operator, I want to set the size of a Session token with `RASTRO_SESSION_TOKEN_BYTES`, so that I choose its length.
29. As an operator, I want to set the name of the CSRF cookie with `RASTRO_CSRF_COOKIE_NAME`, so that it matches the name that my frontend reads.
30. As an operator, I want to set the `Secure`, `HttpOnly`, and `SameSite` flags of the CSRF cookie with `RASTRO_CSRF_COOKIE_SECURE`, `RASTRO_CSRF_COOKIE_HTTPONLY`, and `RASTRO_CSRF_COOKIE_SAMESITE`, apart from the Session cookie, so that each cookie has its own policy.
31. As an operator, I want to set the size of a CSRF token with `RASTRO_CSRF_TOKEN_BYTES`, so that I choose its length.
32. As an operator, I want to set the name of the CSRF header with `RASTRO_CSRF_HEADER_NAME`, so that it matches the header that my frontend sends.
33. As an operator, I want every new setting to default to today's value, so that a deployment that sets none of them behaves as today.
34. As an operator, I want every existing setting except `RASTRO_POSTGRES_URL` to have a default, so that a local run needs only the database URL.
35. As an operator, I want `RASTRO_OPENAPI_ENABLED` to default to `false`, so that a deployment that forgets the variable does not publish the API documentation.
36. As an operator, I want the process to stop at startup without `RASTRO_POSTGRES_URL`, with the variable's name in the error, so that a missing database URL never reaches the first query.
37. As an operator, I want the process to stop at startup when `RASTRO_POSTGRES_URL` uses a scheme other than `postgresql+psycopg`, with the variable's name in the error, so that a wrong driver fails at once.
38. As an operator, I want `.env.example` to list every variable with its value, so that I see every setting in one file.

### API consumer

39. As an API consumer, I want every path, method, status, problem body, and response body of `/api/v1/auth/` to stay the same, so that this change breaks no client.
40. As an API consumer, I want a request with a malformed CSRF header to keep answering `403 csrf_failed`, so that the CSRF value object changes no response.
41. As an API consumer, I want the cookies to keep today's names and flags under the default settings, so that my client keeps working after the upgrade.

### Developer who copies the pattern

42. As a developer who copies the pattern, I want `CODING_STANDARDS.md` to state that a setting holds every value that an operator may change, so that I put a new value in the right place.
43. As a developer who copies the pattern, I want `CODING_STANDARDS.md` to state that a use case receives a configuration value as a keyword-only argument, as it receives a port, so that the domain never reads the settings.
44. As a developer who copies the pattern, I want `CODING_STANDARDS.md` to state the new mapper name rule, so that a new mapper follows it.
45. As a developer who copies the pattern, I want `CODING_STANDARDS.md` to state which value objects hide their value and why, so that a new secret follows the same rule.

### Person who writes a test

46. As a person who writes a test, I want an HTTP test to change one setting through a dependency override, so that a cookie test reads like a request.
47. As a person who writes a test, I want the settings tests to cover each default and each rejection, so that a renamed variable or a lost default fails a test.

## Implementation Decisions

### Secrets

- `RawPassword`, `SessionToken`, and `CsrfToken` hold a Pydantic `SecretStr` as their root value. `repr` shows `**********`. `RawPassword` keeps its minimum length. The hasher, `SessionToken.digest`, the cookie writes, and the CSRF comparison read the value with `get_secret_value()`.
- `Email`, `DisplayName`, `HashedPassword`, and `HashedSessionToken` stay plain values. `SessionGetOutput` sends `email` and `display_name` in its JSON, and a `SecretStr` would send asterisks.
- The `postgres_url` setting is a Pydantic `Secret` that wraps a `PostgresDsn` restricted to the scheme `postgresql+psycopg` by `UrlConstraints`. The engine factory, the Alembic environment, and the root test configuration read it with `get_secret_value()`. A run against the installed Pydantic 2.14 confirmed the type: a valid URL loads and `repr` hides it, while `postgresql://` and `not-a-url` stop the settings with `RASTRO_POSTGRES_URL` in the error.

### Ids

- `Id` is a `RootValueObject` over Pydantic's `PositiveInt` in the common domain's `value_objects` module. In strict mode it rejects `0`, `-1`, `"1"`, and `True`.
- `User.id`, `Session.id`, `Session.user_id`, and the sample app's `Note.id` are `Id`. The rows keep `int` columns, and the infrastructure mappers convert in both directions with `model_validate` on the way in.
- The common infrastructure's `next_id` receives the column object, for example the `id` column of `UserRow`, as the keyword argument `column`, and returns an `Id`. It reads the table and column names from that object, and the constant that holds the text `"id"` goes away.
- `existing_row` receives an `Id`. It still raises `LookupError` for a missing row, and the catch-all handler still answers `{"type": "server.internal_error", "status": 500}`.
- A future id kind, for example a ULID, gets its own value object beside `Id`. It does not use `next_id`, because Python generates it.

### Names

- `user_get_current` becomes `session_get`, `UserGetCurrentOutput` becomes `SessionGetOutput`, and `user_get_current_view` becomes `session_get_view`.
- An application mapper takes the name of its Output DTO in snake case: `session_get_output(user)`.
- `SessionTokenHash` becomes `HashedSessionToken`.
- The `token_hash` field of `Session`, the `token_hash` column of `auth_session`, and the repository lookup `get_by_token_hash` become `hashed_token` and `get_by_hashed_token`. Nothing is deployed, so the agent edits the initial revision of `auth_session` in place.
- The row base keeps the name `Row`, because `Table` collides with `sqlalchemy.Table`.

### Settings

- The settings class gains these fields, each with today's value as its default:

  | Variable | Default |
  |---|---|
  | `RASTRO_SESSION_LIFETIME` | 14 days |
  | `RASTRO_SESSION_COOKIE_NAME` | `rastro_session` |
  | `RASTRO_SESSION_COOKIE_SECURE` | `true` |
  | `RASTRO_SESSION_COOKIE_HTTPONLY` | `true` |
  | `RASTRO_SESSION_COOKIE_SAMESITE` | `lax` |
  | `RASTRO_SESSION_TOKEN_BYTES` | `32` |
  | `RASTRO_CSRF_COOKIE_NAME` | `rastro_csrf` |
  | `RASTRO_CSRF_COOKIE_SECURE` | `true` |
  | `RASTRO_CSRF_COOKIE_HTTPONLY` | `false` |
  | `RASTRO_CSRF_COOKIE_SAMESITE` | `lax` |
  | `RASTRO_CSRF_TOKEN_BYTES` | `32` |
  | `RASTRO_CSRF_HEADER_NAME` | `X-CSRF-Token` |

- The Session lifetime uses the glossary word "lifetime", in place of Django's `SESSION_COOKIE_AGE`. It is a `timedelta`, so the variable accepts an ISO 8601 duration such as `P14D` or a number of seconds.
- Each `SameSite` field accepts only `lax`, `strict`, or `none`.
- The token sizes have no minimum. A small value is the operator's choice.
- The existing settings gain these defaults: `RASTRO_OPENAPI_ENABLED` is `false`, both ZeroMQ addresses are `tcp://127.0.0.1:5555`, `RASTRO_SERVICE_NAMESPACE` and `RASTRO_SERVICE_NAME` are `rastro`, `RASTRO_DEPLOYMENT_ID` is `local`, `RASTRO_DEPLOYMENT_ENVIRONMENT` is `dev`, and `RASTRO_OTEL_GRPC_ENDPOINT` is `localhost:4317`.
- `RASTRO_POSTGRES_URL` stays required with no default, so a deployment that forgets it stops at startup with the variable's name, and no password sits in the code.
- `.env.example` lists every variable with its value, and keeps `RASTRO_OPENAPI_ENABLED=1` for local runs. The compose file keeps the values it sets today.
- `SAFE_METHODS` stays a constant, because the HTTP specification defines the safe methods.

### How a value reaches the code

- `create_app` stores the settings on the app state. A FastAPI dependency in the common presentation's `dependencies` module returns them, and an HTTP test overrides it with `dependency_overrides`.
- `csrf_check`, `csrf_cookie_set`, and the `auth` views read the cookie names, the flags, the header name, and the token sizes from that dependency.
- The views read a cookie with `request.cookies.get(...)` and the name from the settings. FastAPI's `Cookie()` takes its name when Python loads the module, before a request can read the settings.
- The domain never reads the settings. The view passes the Session lifetime and the Session token size to `session_start` as keyword-only arguments. `session_start` calls `SessionToken.generate(nbytes=...)` and passes the lifetime to `Session.start(..., lifetime=...)`. The domain constant `SESSION_LIFETIME` and the constant `SESSION_TOKEN_BYTES` go away.
- The view of `session/start` sets the cookie's `max_age` from the lifetime, as today. The view of `session/end` deletes the cookie with the Session cookie's settings.

### CSRF token

- `CsrfToken` is a value object in the common domain's `value_objects` module, beside `Id`, because the CSRF check protects every app.
- `CsrfToken.generate(nbytes=...)` builds a token with `secrets.token_urlsafe`.
- `CsrfToken` declares no format rule, as `SessionToken` declares none. A header and a cookie always arrive as text, so the value object never fails to parse, and a wrong or missing header keeps answering `403 csrf_failed`.
- `csrf_check` parses the cookie and the header into `CsrfToken` and compares their secret values with `secrets.compare_digest`. A missing or empty cookie and a missing header still raise `CsrfFailedError`.

### Telemetry

- The Session repository stops setting `user.id` on the current span. Its helper functions and their test go away.
- `CODING_STANDARDS.md` keeps the rule that a span never holds personal data, and drops the paragraph that describes the `user.id` attribute.

### Kept as they are

- `import_every_app_module` stays, because the Alembic environment and the worker import every app module through it.
- `main.py` and `worker.py` stay separate. Uvicorn loads the app and taskiq loads the broker, so the worker builds no FastAPI app.
- The value objects stay classes, because mypy cannot tell two `Annotated[str, ...]` aliases apart.

### Cleanup

- The `lifespan` of the app returns `AsyncGenerator[None]` in place of `AsyncIterator[None]`.
- The agent removes every review comment that the maintainer left in the code, because this spec answers each one.
- `CODING_STANDARDS.md`, `README.md`, and `.env.example` change in the same change as the code they describe.

## Testing Decisions

### What makes a good test

- A good test exercises behaviour through a public seam and asserts what a caller observes: a return value, a raised error, an HTTP status, a response body, a cookie, or a validation message.
- A test that breaks when a private helper is renamed tests the implementation, and is rewritten.
- An HTTP test changes a setting through `dependency_overrides`. The settings tests set environment variables, as they do today.

### Seams

The maintainer confirmed four existing seams and no new one:

1. **The settings seam** covers each default, the `false` default of `RASTRO_OPENAPI_ENABLED`, the stop without `RASTRO_POSTGRES_URL`, the stop on a `postgresql://` URL, and a `repr` of the settings that hides the database password. The test that requires every variable of `.env.example` now requires only `RASTRO_POSTGRES_URL`.
2. **The HTTP seam** overrides the settings dependency with other values, for example another cookie name, `secure=false`, and another lifetime, and checks the cookie that the response sets. It also checks that a malformed CSRF header answers `403 csrf_failed` and that the JSON of `GET /session` does not change.
3. **The domain seam** covers `Id` with `0` and `-1`, the length of the tokens from `SessionToken.generate` and `CsrfToken.generate`, and a `repr` of `RawPassword`, `SessionToken`, and `CsrfToken` that shows `**********`.
4. **The repository seam** covers `next_id` returning an `Id`, and a row with id `0` that fails when it becomes an aggregate.

### Prior art

- The settings tests show the environment setup and the assertions on the error text.
- The HTTP tests of the `auth` test package show the literal problem assertions and the cookie assertions.
- The domain tests of `Session` and the value objects show pure tests with no fake.
- The repository tests show the corrupted-row case and the `next_id` case.

## Out of Scope

- Any change to the paths, methods, statuses, problem bodies, and response bodies of `/api/v1/auth/`.
- Settings for the cookie domain and the cookie path. They come when a frontend on another subdomain exists.
- A minimum size for the tokens.
- A setting for the safe HTTP methods.
- A value object per aggregate id, such as `UserId`.
- A `fastapi.Cookie` parameter for the cookies.
- Merging `main.py` and `worker.py`.
- Removing `import_every_app_module`.
- Renaming `Row` to `Table`.
- `Annotated` aliases in place of value object classes.

## Further Notes

- The grilling session settled the decisions above. An agent implements this spec in auto mode and never stops to ask the user. When it finds a gap, it picks the option that fits this spec, `CODING_STANDARDS.md`, and the ADRs best, applies it, updates `CODING_STANDARDS.md` in the same change, and records the decision. Each record names the gap, the option chosen, and the options rejected.
- These decisions came from synthesis, not from the grilling, and the agent reports them first:
  - The `token_hash` field, column, and lookup become `hashed_token`, so that they match the rename of `HashedSessionToken` and the rule that a row, an aggregate, and a value object share one name.
  - The sample app's `Note.id` uses `Id`, because the maintainer asked that every aggregate use it.
  - A use case receives a configuration value as a keyword-only argument, beside its ports.
  - A FastAPI dependency returns the settings, so that an HTTP test changes a setting through `dependency_overrides`.
  - The view of `session/end` deletes the Session cookie with the Session cookie's settings.
- The decisions of the earlier spec that the maintainer accepted in this review stay as they are: the import lines changed in four `auth` test modules, one error-to-status table per app, the `add` translation of `auth_user_email_key` only, the removed `user_register` service tests, and the `skip_dep_check` of the SQLAlchemy instrumentation.
