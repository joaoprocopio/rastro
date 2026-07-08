# rastro

An experimental Django service used to explore two things at once:

- **Domain-driven design** — tactical patterns (aggregates, value objects, use cases,
  repositories, mappers) layered per bounded context.
- **Observability** — full [OpenTelemetry](https://opentelemetry.io/) instrumentation feeding a
  self-hosted **Grafana + ClickHouse** stack via the OpenTelemetry Collector.

## Stack

| Concern        | Technology                                                    |
| -------------- | ------------------------------------------------------------- |
| Web framework  | Django 6 (Gunicorn, Argon2 password hashing)                  |
| Language       | Python 3.14, managed with [uv](https://docs.astral.sh/uv/)    |
| Validation     | Pydantic 2 (domain value objects & DTOs)                      |
| Database       | PostgreSQL                                                    |
| Telemetry      | OpenTelemetry SDK + OTLP exporter (Django, logging, psycopg2) |
| Collector      | OpenTelemetry Collector (contrib)                             |
| Storage (o11y) | ClickHouse                                                    |
| Dashboards     | Grafana (provisioned ClickHouse datasource + dashboards)      |
| Tooling        | Ruff (lint), mypy `--strict` (types), pytest (+ coverage)     |

## Architecture

Code lives under `src/`, split into three top-level packages:

- **`rastro`** — the Django project and the `iam` (Identity & Access Management) bounded
  context, organized in DDD layers:
  - `domain/` — aggregates, value objects, domain services, repository interfaces, errors
  - `application/` — use cases and their input/output DTOs
  - `infrastructure/` — repository/service implementations and DI composition (factories)
  - `presentation/` — Django views and URL routing
- **`rastro_base`** — reusable framework primitives: `Entity`, `Aggregate`, `RootValueObject`,
  DTO/`RootModel` bases, `Mapper`, `UseCase`, and RFC 7807 error → `Problem` handling.
- **`rastro_shared_kernel`** — cross-cutting helpers shared across contexts (typed `get_env`,
  parsers, shared value objects).

Errors raise as typed `BaseError`s and are serialized globally into RFC 7807 `Problem`
JSON responses.

## Running the full stack

Everything is wired in `compose.yaml` — Django, Postgres, the OTel Collector, ClickHouse, and
Grafana:

```sh
docker compose up --build
```

The Django container runs migrations and `collectstatic` on start, then serves via Gunicorn.

| Service           | URL                     |
| ----------------- | ----------------------- |
| Django API        | http://localhost:8000   |
| Grafana           | http://localhost:7141   |
| ClickHouse (HTTP) | http://localhost:8123   |
| Postgres          | localhost:5432          |
| OTel Collector    | gRPC :4317 / HTTP :4318 |

Telemetry flows: **Django → OTel Collector → ClickHouse → Grafana**. Grafana ships with the
ClickHouse datasource and dashboards pre-provisioned from `docker/grafana/provisioning/`.

## Local development

```sh
uv sync                              # install dependencies (incl. dev group)
uv run python manage.py migrate      # apply migrations (needs a reachable Postgres)
uv run python manage.py runserver    # start the dev server
```

Configuration is read from environment variables (see `RASTRO_DJANGO_*` in `compose.yaml` for the
full set), including `RASTRO_DJANGO_SECRET_KEY`, `RASTRO_DJANGO_DEBUG`, the `RASTRO_DJANGO_POSTGRES_*`
database settings, and the `RASTRO_DJANGO_OTEL_*` collector endpoints.

## API

The `iam` context is mounted under `/api/v1/iam/`, resource-oriented around an `identities`
collection and a `session` singleton:

| Method | Path                        | Purpose                              |
| ------ | --------------------------- | ------------------------------------ |
| POST   | `/api/v1/iam/identities`    | Register a new identity (auto sign-in) |
| POST   | `/api/v1/iam/session`       | Authenticate (start a session)       |
| GET    | `/api/v1/iam/session`       | Resolve the current identity         |
| DELETE | `/api/v1/iam/session`       | End the current session              |
| GET    | `/api/v1/iam/csrftoken`     | Issue a CSRF token                   |

Django admin is served at `/admin/`.

## Checks

```sh
uv run ruff check src/            # lint
uv run mypy src/                  # static type-checking (strict)
uv run pytest                     # tests (with coverage over src/)
uv run python manage.py check     # Django system checks
```
