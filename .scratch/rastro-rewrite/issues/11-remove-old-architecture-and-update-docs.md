# 11: Remove the old architecture and update the docs

**What to build:** Delete what remains of the DDD architecture and make the docs describe the new pattern, so that a developer who copies rastro finds one pattern, the same one in the code and in the docs. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

After tickets 08 and 10, no endpoint uses the old layers. This ticket deletes them and completes the checks:

- the `domain`, `application`, `infrastructure`, `presentation`, and `shared` subpackages of `iam`;
- the rest of `rastro_base` and `rastro_shared_kernel`;
- the `model_bakery` dependency and the old fixtures in the root `conftest.py`, which factories replace.

**Blocked by:** 02 (Telemetry without personal data), 08 (Identity registration), 10 (Current Session, end of Session, and the CSRF cookie)

**Status:** resolved

- [x] The old `iam` subpackages, `rastro_base`, and `rastro_shared_kernel` no longer exist, and nothing imports them.
- [x] `model_bakery` is no longer a dependency, and every test builds its data with factory_boy factories.
- [x] The import-linter contracts match the full list in the spec's "Tooling" section, and they pass.
- [x] The `rastro` package holds only the settings package, the root URLconf, the WSGI and ASGI entry points, and the telemetry setup.
- [x] The Checks section of `README.md` lists every check.
- [x] `CODING_STANDARDS.md` no longer says that some code predates the rewrite.
- [x] A final HTTP run covers the five operations of the spec's HTTP contract from end to end.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [x] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket-11`, before the merge of `rastro-rewrite`:

- `src/rastro/iam/application/`, `src/rastro/iam/domain/`, `src/rastro/iam/shared/` (with `test_mappers.py`), `src/rastro_base/`, and `src/rastro_shared_kernel/` are deleted, and the stale `__pycache__` directories of `infrastructure/` and `presentation/` with them. A `grep` for `rastro_base`, `rastro_shared_kernel`, `model_bakery`, and `bakery` over every `.py`, `.toml`, `.md`, `.yaml`, and the `dockerfile` finds nothing outside `.scratch/`.
- `uv remove --group dev model-bakery` dropped the package from `pyproject.toml` and `uv.lock`. The root `conftest.py` keeps the `identity` fixture, which already used `IdentityFactory`, and loses `anonymous_user`, which no test asked for.
- The six contracts in `[tool.importlinter]` cover the spec's "Tooling" list with two parts in `tests/architecture/`, as ticket 06 recorded: `django.conf` in `test_services_and_selectors.py`, and the standard library rule of `values.py` in `test_values.py`. I tried `"rastro"` as a forbidden module for `rastro.*.values` with `rastro.*.values -> rastro.common.values` ignored; `lint-imports` accepted it but reported a temporary `from rastro.iam.models import Identity` in `values.py` only through its indirect chain to `django`, so the entry adds nothing and stays out. The ticket 07 `ignore_imports` for `models -> services` and `models -> deps` stay.
- `src/rastro/` holds `settings/`, `urls.py`, `wsgi.py`, `asgi.py`, `telemetry.py`, the apps `common/` and `iam/`, and `tests/test_telemetry.py`, which moved from the old `__tests__/` directory to the `tests/` package layout that `rastro/common` uses.
- The Checks section of `README.md` already lists `docker compose up -d postgres`, `uv sync`, `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, `pytest`, and `manage.py check`, and holds no architecture description, so it is unchanged. `RASTRO_DEBUG=1 uv run python manage.py check` reports no issues.
- `CODING_STANDARDS.md` loses the sentence about code that predates the rewrite. The protocol check example reads `_authenticator: Authenticator = django_authenticate`, named after the port, with the `no-redef` reason, as `adapters.py` does. The import-linter bullet says that `values` imports neither Django nor Pydantic, and the pytest bullet names the standard library check of `values.py`. `session_start` and `session_end` carry `@transaction.atomic`, as the rule says, so that rule is unchanged.
- `src/rastro/iam/tests/apis/test_end_to_end.py` walks the five operations with `Client(enforce_csrf_checks=True)`: `GET /csrf` answers `204` and sets `csrftoken`; `POST /identities/register` with `" Ada@Example.com"` answers `201`; `GET /session` answers `401` `iam.not_authenticated`; `POST /session/start` with `ada@example.com` answers `204` and sets the session cookie; `GET /session` answers `200` with `email` and `display_name`; `POST /session/end` answers `204`; and `GET /session` answers `401` again. Each POST reads the token from the `csrftoken` cookie, because Django rotates it on login. A copy of the test without the `X-CSRFToken` header failed with `403` on the registration, so the CSRF step is real.
- The gate: `ruff check`, `ruff format --check`, `mypy`, `lint-imports` (6 kept, 0 broken), and `pytest` (138 passed: 142 before, plus 1, minus the 5 mapper tests) are green. `docker compose build django` builds the image. I did not run `docker compose up --build`, because the ports belong to the main directory; the merger runs the full stack.

## Answer

Merged into `rastro-rewrite` in `af64d7c`. The merge ran the full check gate and a smoke run of the built image against a fresh database.
