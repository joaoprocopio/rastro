# 01: Give every setting a default and keep the database URL secret

**What to build:** An operator runs rastro with `RASTRO_POSTGRES_URL` as the only variable, and every other setting takes its default, the 12 new cookie, CSRF, and Session settings included. The database URL hides its password in `repr` and accepts only the `postgresql+psycopg` scheme. A FastAPI dependency returns the settings, so tickets 03 and 04 read their values from it. Read the spec (`.scratch/layered-architecture-review/spec.md`, sections Settings, Secrets, and How a value reaches the code), `CODING_STANDARDS.md`, and the ADRs before you start, and follow the auto mode that the spec's Further Notes describe.

Declare every new setting with the default from the spec's table, and give the existing settings the defaults that the spec lists. Keep `RASTRO_POSTGRES_URL` required. Store the settings on the app state in `create_app`, and add the dependency that returns them to the common presentation's `dependencies` module. Annotate the `lifespan` of the app as an async generator. Update `.env.example`, the README, and the settings tests.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] With only `RASTRO_POSTGRES_URL` set, the settings load, and each other setting equals its default from the spec.
- [x] Without `RASTRO_POSTGRES_URL`, the process stops at startup, and the error names `RASTRO_POSTGRES_URL` and shows no value.
- [x] With `RASTRO_POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/postgres`, the process stops at startup, and the error names the variable.
- [x] `repr` of the settings shows no database password.
- [x] Without `RASTRO_OPENAPI_ENABLED`, `GET /openapi.json` answers `404`.
- [x] The settings dependency returns the settings that `create_app` received.
- [x] `.env.example` lists every variable with its value.
- [x] `docker compose up` serves the app and the worker.
- [x] Every check in the README passes.

## Comments

### Decisions

- **The settings dependency and where it lives.** `app_settings(request: Request) -> Settings` in `rastro/common/presentation/dependencies.py` reads `request.app.state.settings`, which `create_app` stores. The alias `AppSettings = Annotated[Settings, Depends(app_settings)]` sits beside `DatabaseSession`. A view or a dependency declares a parameter `settings: AppSettings`, and an HTTP test overrides it with `app.dependency_overrides[app_settings] = lambda: other_settings`. Tickets 03 and 04 import `AppSettings` and `app_settings` from that module. Rejected: a function named `settings`, because it shadows the `settings` parameter of every view and fixture; a `lru_cache` function that calls `Settings()`, because a test could not pass the settings that `create_app` received.
- **The field names of the new settings.** Each field is the variable name without `RASTRO_`, in lower case: `session_lifetime`, `session_cookie_name`, `session_cookie_secure`, `session_cookie_httponly`, `session_cookie_samesite`, `session_token_bytes`, `csrf_cookie_name`, `csrf_cookie_secure`, `csrf_cookie_httponly`, `csrf_cookie_samesite`, `csrf_token_bytes`, and `csrf_header_name`. The `SameSite` fields have the type `rastro.settings.SameSite`, which is `Literal["lax", "strict", "none"]` and matches the `samesite` argument of Starlette's `set_cookie`. Rejected: a nested model per cookie, because the spec's table names flat variables.
- **A number of seconds for `RASTRO_SESSION_LIFETIME`.** Pydantic 2.14 parses `P14D` from text but rejects `"3600"`, so the spec's "or a number of seconds" fails with a bare `timedelta`. The field type `Duration` in `rastro/settings.py` converts a text of digits to an `int` before Pydantic parses it. Rejected: only an ISO 8601 duration, because the spec promises seconds and a Django operator thinks in seconds.
- **How code reads the database URL.** The engine factory, the Alembic environment, and the root `conftest.py` call `str(settings.postgres_url.get_secret_value())`. The root `settings` fixture wraps the URL of its test database in `Secret(PostgresDsn(...))`. Rejected: a property on `Settings` that returns the plain URL, because it would let a log print the password again.
- **The value of `RASTRO_DEPLOYMENT_ID` in `.env.example`.** It keeps `2f92ca37`, and `.env.example` writes the lifetime as `P14D` and the flags as `1` and `0`, like `RASTRO_OPENAPI_ENABLED`. Rejected: the default `local`, because the line already existed and the spec changes only the code default.
- **The test that `.env.example` lists every variable.** `test_env_example_lists_every_variable` compares the names in `.env.example` with the aliases of `Settings.model_fields`, so a new field without a line fails. The parametrized test of every required variable goes away, and `test_every_setting_but_the_postgres_url_has_a_default` replaces it. Rejected: a test per variable that deletes it, because a deleted variable now takes its default.
- **The compose acceptance criterion.** The agent did not run `docker compose up`. It ran `uvicorn rastro.main:app` and `taskiq worker rastro.worker:broker -w 1` with only `RASTRO_POSTGRES_URL` set: both started, `GET /openapi.json` answered `404`, and `GET /api/v1/auth/csrf` set the `rastro_csrf` cookie with `Secure` and `SameSite=lax`. `compose.yaml` keeps every value it set, so its services read the same settings as before.

### Compose check

`docker compose up --build` against the shared `postgres` database stopped in `migrate` with `Can't locate revision identified by '23f46a63b6b5'`. That database holds a revision that commit `d39ea2f` deleted, so the failure predates this ticket. Against a fresh database, `migrate` exited `0`, the API and the worker started, `GET /openapi.json` answered `404`, and register, `session/start`, `GET /session`, and `session/end` answered as the HTTP tests expect, with the default cookie names and flags.
