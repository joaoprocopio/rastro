# 03: Building blocks in rastro.common

**What to build:** Create the `rastro.common` package with the building blocks that every app reuses, and move the environment helpers into it, so that later tickets build value objects and models on one shared base. This is a prefactor: no behaviour changes for a person who uses rastro. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The building blocks are:

- `StrValueObject`, the base of a value object that wraps one string. It teaches Pydantic to parse a string into the value object and to serialize it back to a string, and it is the only part of a value object that knows Pydantic.
- `InvalidValueError`, a `ValueError` subclass that carries a stable code, so that Pydantic reports it as a field error and the code survives in the error context.
- `StrEnumField`, a generic model field that stores a `StrEnum`, builds its `choices` with `str_enum_to_choices`, returns the enum when Django reads from the database, and supports migrations.
- `BaseModel`, an abstract model with `created_at` and `updated_at`.
- `get_env`, `parse_csv`, `parse_booleanish`, and `str_enum_to_choices`, moved from `rastro_shared_kernel` with their tests.

**Blocked by:** 01 (Settings package and the RASTRO_ prefix)

**Status:** resolved

- [x] Pure tests, with no database, show that a `StrValueObject` subclass parses from a JSON string inside a Pydantic model, serializes back to a plain string, and turns an `InvalidValueError` into a Pydantic field error whose context still holds the code.
- [x] A test shows that a non-string input fails as a type error before the value object runs.
- [x] A test shows that `StrEnumField` returns the enum member on read, rejects an unknown value, and produces a migration that names the enum.
- [x] `BaseModel` sets `created_at` on creation and updates `updated_at` on save.
- [x] The settings import the environment helpers from `rastro.common`, and the moved tests pass there.
- [x] `rastro_shared_kernel` keeps only what the old `iam` code still imports. Everything that moved is deleted from it.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [x] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Branch `ticket-03`, worktree `/home/jao/workspace/joaoprocopio/rastro-wt/ticket-03`. I verified each box through the gate or by hand:

- `rastro.common` has one module per role: `values.py` (`StrValueObject`, `InvalidValueError`), `fields.py` (`StrEnumField`, `str_enum_to_choices`), `models.py` (`BaseModel`), and `env.py` (`get_env`, `parse_csv`, `parse_booleanish`). `str_enum_to_choices` lives next to the field that uses it, so `env.py` imports no Django.
- `src/rastro/common/tests/test_values.py` runs with no database. A `Color` subclass parses from `{"color": "red"}`, dumps back to `{"color": "red"}`, and an invalid value becomes a `value_error` at `("color",)` whose `ctx["error"].code` is the code of the `InvalidValueError`. A JSON number fails with `string_type` before the value object runs.
- `src/rastro/common/tests/test_fields.py` reads a `Post` back from the database and gets `Status.PUBLISHED`, rejects `"archived"` on write, on `from_db_value`, and on `to_python` (as a `ValidationError` with code `invalid_choice`), and `MigrationWriter.serialize(field)` names `rastro.common.tests.sample.models.Status` with `kwargs == {"enum": Status}`.
- `src/rastro/common/tests/test_models.py` shows `created_at` set on creation and `updated_at` greater after a second `save()`.
- The sample model lives in the test-only app `rastro.common.tests.sample`, which only `rastro.settings.test` installs. mypy resolves `Post.status` as `Status`.
- The settings import from `rastro.common.env`. `grep rastro_shared_kernel.env src/` finds nothing. The moved tests pass under `src/rastro/common/tests/test_env.py`.
- `rastro_shared_kernel` keeps `__init__.py` and `value_objects.py` (`Id`), which the old `iam` domain, repositories, DTOs, and mappers still import. `env.py`, `utils.py`, and `__tests__/` are gone.
- The gate is green: `ruff check`, `ruff format --check`, `mypy` (66 files), and `pytest` (61 tests) with `RASTRO_POSTGRES_DB=ticket_03`.
- The brief forbids `docker compose up` in a worktree, so I ran `docker compose build django` and served the image with `docker run --network host` against the `ticket_03` database on port 8003: `migrate` applied every migration, `GET /admin/login/` answered `200`, and `GET /api/v1/iam/session` answered `401`. The merger runs the full stack on the integration branch.

## Answer

Merged into `rastro-rewrite` in `4daa1be`. The merge ran the full check gate and a smoke run of the built image against a fresh database.
