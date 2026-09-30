# rastro

rastro is an experimental FastAPI service for OpenTelemetry and Grafana instrumentation. Its layout follows [Netflix Dispatch](https://github.com/Netflix/dispatch): one package per feature, each with its own `models.py`, `service.py`, and `views.py`.

The OpenTelemetry instrumentation is not wired in yet. The compose file still starts the OpenTelemetry Collector, ClickHouse, and Grafana, but the API sends them nothing.

## Stack

| Concern       | Technology                                                    |
| ------------- | ------------------------------------------------------------- |
| Web framework | FastAPI with sync views, served by Uvicorn (`fastapi run`)    |
| Language      | Python 3.14, managed with [uv](https://docs.astral.sh/uv/)    |
| Validation    | Pydantic 2 in strict mode, pydantic-settings for config       |
| Database      | PostgreSQL through SQLAlchemy 2 (sync ORM) and psycopg 3      |
| Migrations    | Alembic                                                       |
| Passwords     | Argon2id through argon2-cffi                                  |
| Tooling       | Ruff, mypy and Pyright in strict mode, pytest with coverage   |

## Architecture

The code lives in one package, `src/rastro`:

- `main.py` builds the app: middleware, exception handlers, and the `/api/v1` router.
- `api.py` mounts every feature router under one parent router, which runs the CSRF check on every route.
- `config.py` reads the `RASTRO_*` environment variables into a typed `Settings`.
- `database/core.py` holds the engine, the declarative `Base`, and the `DbSession` dependency. `database/revisions/` holds the Alembic migrations.
- `exceptions.py` and `problem.py` turn every error into an [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) `application/problem+json` response.
- `security.py` holds the CSRF tokens, the security headers, and the cookie names.
- `iam/` is the Identity and Access Management feature: `models.py`, `service.py`, `views.py`, and `password.py`, plus the `session/` sub-feature.

A feature's `service.py` holds plain functions that take a keyword-only `db_session`, as in Dispatch. A view calls them, and the `DbSession` dependency commits the transaction when the view returns, or rolls it back when the view raises.

## Authentication

The API signs people in with an email and a password, and keeps the session on the server. The design follows the OWASP cheat sheets for authentication, session management, password storage, and CSRF prevention:

- Argon2id hashes each password with 19 MiB of memory, 2 iterations, and 1 degree of parallelism. A sign-in rehashes a password stored with older parameters.
- A sign-in with an unknown email, a wrong password, or an inactive identity gets the same `401` body after the same hashing work, so the response does not reveal which emails exist.
- The session token is 256 random bits in an `HttpOnly`, `Secure`, `SameSite=Lax` cookie. The database stores its SHA-256 digest, never the token.
- Each sign-in issues a new token and deletes the previous session. A session ends after 30 minutes without a request, or 12 hours after the sign-in.
- Every unsafe request (`POST`, `PUT`, `PATCH`, `DELETE`) needs the `csrftoken` cookie echoed in the `X-CSRFToken` header. The token is an HMAC bound to the session, so it changes at every sign-in and sign-out. A request whose `Origin` is neither the API's own origin nor in `RASTRO_CSRF_TRUSTED_ORIGINS` gets a `403`.

## API

The `iam` feature is mounted under `/api/v1/iam/`, around an `identities` collection and a `session` singleton:

| Method | Path                     | Purpose                                | Success                 |
| ------ | ------------------------ | -------------------------------------- | ----------------------- |
| POST   | `/api/v1/iam/identities` | Register a new identity, and sign in   | `201`, public identity  |
| POST   | `/api/v1/iam/session`    | Sign in with an email and a password   | `200`, public identity  |
| GET    | `/api/v1/iam/session`    | Return the identity of the session     | `200`, or `401`         |
| DELETE | `/api/v1/iam/session`    | End the session                        | `204`                   |
| GET    | `/api/v1/iam/csrftoken`  | Set the `csrftoken` cookie             | `204`                   |

With `RASTRO_DEBUG=1`, the app serves the OpenAPI docs at `/api/docs`.

## Run the full stack

`compose.yaml` starts the API, Postgres, the OpenTelemetry Collector, ClickHouse, and Grafana:

```sh
docker compose up --build
```

The API container runs `alembic upgrade head`, then serves on port 8000 with 4 Uvicorn workers.

| Service           | URL                     |
| ----------------- | ----------------------- |
| API               | http://localhost:8000   |
| Grafana           | http://localhost:7141   |
| ClickHouse (HTTP) | http://localhost:8123   |
| Postgres          | localhost:5432          |
| OTel Collector    | gRPC :4317 / HTTP :4318 |

## Develop locally

The app reads its configuration from `RASTRO_*` environment variables, or from a `.env` file in the working directory. `RASTRO_SECRET_KEY` has no default and needs at least 32 characters. The fields of `Settings` in `src/rastro/config.py` list every variable with its default.

To serve plain HTTP on a host other than `localhost`, set `RASTRO_COOKIE_SECURE=0`, because the browser drops a `Secure` cookie over HTTP.

```sh
uv sync                     # install the dependencies, dev group included
uv run alembic upgrade head # migrate the database
uv run fastapi dev          # serve with auto-reload on port 8000
```

To add a migration after you change a model, generate it and review the file before you commit it:

```sh
uv run alembic revision --autogenerate -m "describe the change"
```

## Checks

The tests need a Postgres that the `RASTRO_POSTGRES_*` variables point at. The suite creates and drops its own `rastro_test` database there.

```sh
uv run ruff check           # lint
uv run ruff format --check  # format
uv run mypy src conftest.py # type-check with mypy, strict
uv run pyright              # type-check with Pyright, strict
uv run pytest               # test, with coverage over src/
uv run alembic check        # fail if the models and migrations differ
```
