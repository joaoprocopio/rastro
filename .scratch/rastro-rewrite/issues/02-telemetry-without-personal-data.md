# 02: Telemetry without personal data

**What to build:** Stop sending personal data to ClickHouse and instrument every way of running rastro, so that an operator who watches Grafana sees complete telemetry that holds no email address and no password hash. Read the spec (`.scratch/rastro-rewrite/PRD.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

Today the Django request span records the Identity's email, the psycopg2 instrumentation records SQL parameters (which include password hashes), and only the WSGI entry point calls the telemetry setup.

**Blocked by:** 01 (Settings package and the RASTRO_ prefix)

**Status:** ready-for-agent

- [ ] The request span records the Identity's id as `enduser.id` and never records the email.
- [ ] A request without a Session records no `enduser.id`.
- [ ] The psycopg2 instrumentation no longer captures query parameters.
- [ ] The WSGI entry point, the ASGI entry point, and `manage.py` all call the telemetry setup, once each.
- [ ] Telemetry settings come from the telemetry settings module.
- [ ] A test covers the span attributes of an authenticated request and of an anonymous one.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
