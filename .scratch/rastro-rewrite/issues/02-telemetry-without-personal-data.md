# 02: Telemetry without personal data

**What to build:** Stop sending personal data to ClickHouse and instrument every way of running rastro, so that an operator who watches Grafana sees complete telemetry that holds no email address and no password hash. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

Today the Django request span records the Identity's email, the psycopg2 instrumentation records SQL parameters (which include password hashes), and only the WSGI entry point calls the telemetry setup.

**Blocked by:** 01 (Settings package and the RASTRO_ prefix)

**Status:** ready-for-agent

- [x] The request span records the Identity's id as `enduser.id` and never records the email.
- [x] A request without a Session records no `enduser.id`.
- [x] The psycopg2 instrumentation no longer captures query parameters.
- [x] The WSGI entry point, the ASGI entry point, and `manage.py` all call the telemetry setup, once each.
- [x] Telemetry settings come from the telemetry settings module.
- [x] A test covers the span attributes of an authenticated request and of an anonymous one.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Branch `ticket-02`, head after the entry point commit. I verified each box by hand or through the gate:

- `src/rastro/telemetry.py` records `enduser.id` in the response hook from `request.user.pk` and reads no email field. `src/rastro/__tests__/test_telemetry.py` passes an in-memory exporter to `telemetry.instrument_django` and reads the server span of `GET /api/v1/iam/session` through the test `Client`: after `force_login`, `enduser.id` equals the Identity's id and no attribute value equals the email. Without a Session, the span has no `enduser.id`.
- `Psycopg2Instrumentor().instrument(capture_parameters=False)` is the only psycopg2 call. No test covers it, because the Django test connection opens before the instrumentation wraps `psycopg2.connect`.
- `src/rastro/wsgi.py`, `src/rastro/asgi.py`, and `manage.py` each call `telemetry.instrument()` once. `instrument` returns on a second call, because `manage.py runserver` imports `rastro.wsgi` in the same process. With `runserver` on port 8002, the log held no "already instrumented" and no "Overriding of current TracerProvider" line, and `GET /api/v1/iam/session` answered `401`. `manage.py check` and `manage.py migrate` ran with the exporters active.
- Every value that `telemetry.py` reads comes from `rastro.settings.telemetry`.
- The gate is green: `ruff check`, `ruff format --check`, `mypy`, and `pytest` with 50 tests under `RASTRO_POSTGRES_DB=ticket_02`.

One box stays open:

- "`docker compose up --build` starts the stack": the implementer brief forbids `docker compose up` in a worktree. I ran `docker compose build django` and served the image with `docker run --network host` against the `ticket_02` database on port 8003: `migrate` and `collectstatic` ran, gunicorn booted two workers, `GET /api/v1/iam/csrftoken` answered `200`, and `GET /api/v1/iam/session` answered `401`. The merger runs the full stack on the integration branch.
