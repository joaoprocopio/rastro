# 01: Settings package and the RASTRO_ prefix

**What to build:** Split the single settings module into a settings package and rename every environment variable to the `RASTRO_` prefix, so that each setting has one obvious home and a missing variable can never run production in debug mode. The app behaves the same for a person who uses it. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The package has a base module with every setting, a test module that overrides values for the test run (including a fast password hasher), a telemetry module, and a sessions module. No setting exists only in production. Environment variables, read with `get_env`, switch features on and off.

This ticket also prepares the tooling that later tickets rely on: ruff bans `django.dispatch.receiver` and `csrf_exempt` through `TID251`, and factory_boy is a dev dependency.

**Blocked by:** None (can start immediately)

**Status:** in-review

- [x] Settings live in a package with base, test, telemetry, and sessions modules, and each setting is defined once.
- [x] Every environment variable uses the `RASTRO_` prefix in place of `RASTRO_DJANGO_`, in the settings, `compose.yaml`, and the tests.
- [x] `DEBUG` defaults to off. Without `DEBUG`, a missing `SECRET_KEY` stops the app at startup, and `SECRET_KEY` has no insecure default.
- [x] `CSRF_COOKIE_HTTPONLY` is `False` and appears once.
- [x] The unused `OTEL_HTTP_ENDPOINT` setting is gone.
- [ ] pytest runs with the test settings module, and the type checker uses the base module.
- [x] ruff fails on an import of `django.dispatch.receiver` or `csrf_exempt`.
- [x] factory_boy is installed as a dev dependency.
- [x] Every existing HTTP test still passes without a change to its assertions.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Branch `ticket-01`, head after the settings commit. I verified each box by hand or through the gate:

- `src/rastro/settings/` holds `base.py`, `test.py`, `telemetry.py`, and `sessions.py`. `base.py` star-imports the telemetry and sessions modules, so it exposes every setting while each one is written once. `sessions.py` holds the CSRF cookie settings, because the single-page app reads the CSRF token from a cookie as part of its Session flow.
- `grep RASTRO_DJANGO` finds nothing outside `.scratch/`. The tests had no reference to an environment variable before this ticket; `test.py` now sets `RASTRO_SECRET_KEY` for the test run.
- `env -u RASTRO_SECRET_KEY -u RASTRO_DEBUG python -c "import rastro.settings.base"` raises `ImproperlyConfigured: Set RASTRO_SECRET_KEY when RASTRO_DEBUG is off.` With `RASTRO_DEBUG=1` and no key, `SECRET_KEY` is a random key from `get_random_secret_key()`, so no fixed value ships in the code.
- `CSRF_COOKIE_HTTPONLY = False` appears once, in `sessions.py`. `OTEL_HTTP_ENDPOINT` is gone from the settings and from `compose.yaml`.
- ruff reports `TID251` on a probe file that imports `django.dispatch.receiver` and `csrf_exempt`, with the messages from `pyproject.toml`.
- `factory-boy` is in the `dev` group of `pyproject.toml` and in `uv.lock`.
- The 10 HTTP tests in `src/rastro/iam/presentation/__tests__/test_views.py` pass unchanged. pytest ran 48 tests with `RASTRO_POSTGRES_DB=ticket_01`.
- The gate is green: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.

Two boxes stay open:

- "the type checker uses the base module": mypy points at `rastro.settings.test`. The django-stubs plugin imports the settings module to learn `AUTH_USER_MODEL` and the custom settings, and `base.py` raises without `RASTRO_SECRET_KEY` in the shell, so `uv run mypy src/` fails with "Error constructing plugin instance of NewSemanalDjangoPlugin". The test module imports `base.py` and supplies the key. The alternative is to keep `base.py` for mypy and run the gate as `RASTRO_DEBUG=1 uv run mypy src/`. The user decides.
- "`docker compose up --build` starts the stack": the implementer brief forbids `docker compose up` in a worktree, because the main directory owns the ports. I ran `docker compose build django` and then served the built image with `docker run --network host` against the `ticket_01` database on port 8001: `migrate` applied every migration, `GET /api/v1/iam/csrftoken` answered `200`, and `GET /api/v1/iam/session` answered `401`. The merger runs the full stack on the integration branch.

The README now lists `ruff format --check` and runs `manage.py check` with `RASTRO_DEBUG=1`, because the command fails without a secret key or debug mode.
