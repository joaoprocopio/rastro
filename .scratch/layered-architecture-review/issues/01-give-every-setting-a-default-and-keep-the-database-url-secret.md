# 01: Give every setting a default and keep the database URL secret

**What to build:** An operator runs rastro with `RASTRO_POSTGRES_URL` as the only variable, and every other setting takes its default, the 12 new cookie, CSRF, and Session settings included. The database URL hides its password in `repr` and accepts only the `postgresql+psycopg` scheme. A FastAPI dependency returns the settings, so tickets 03 and 04 read their values from it. Read the spec (`.scratch/layered-architecture-review/spec.md`, sections Settings, Secrets, and How a value reaches the code), `CODING_STANDARDS.md`, and the ADRs before you start, and follow the auto mode that the spec's Further Notes describe.

Declare every new setting with the default from the spec's table, and give the existing settings the defaults that the spec lists. Keep `RASTRO_POSTGRES_URL` required. Store the settings on the app state in `create_app`, and add the dependency that returns them to the common presentation's `dependencies` module. Annotate the `lifespan` of the app as an async generator. Update `.env.example`, the README, and the settings tests.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] With only `RASTRO_POSTGRES_URL` set, the settings load, and each other setting equals its default from the spec.
- [ ] Without `RASTRO_POSTGRES_URL`, the process stops at startup, and the error names `RASTRO_POSTGRES_URL` and shows no value.
- [ ] With `RASTRO_POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/postgres`, the process stops at startup, and the error names the variable.
- [ ] `repr` of the settings shows no database password.
- [ ] Without `RASTRO_OPENAPI_ENABLED`, `GET /openapi.json` answers `404`.
- [ ] The settings dependency returns the settings that `create_app` received.
- [ ] `.env.example` lists every variable with its value.
- [ ] `docker compose up` serves the app and the worker.
- [ ] Every check in the README passes.

## Comments
