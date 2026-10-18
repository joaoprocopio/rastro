# 03: Building blocks in rastro.common

**What to build:** Create the `rastro.common` package with the building blocks that every app reuses, and move the environment helpers into it, so that later tickets build value objects and models on one shared base. This is a prefactor: no behaviour changes for a person who uses rastro. Read the spec (`.scratch/rastro-rewrite/PRD.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The building blocks are:

- `StrValueObject`, the base of a value object that wraps one string. It teaches Pydantic to parse a string into the value object and to serialize it back to a string, and it is the only part of a value object that knows Pydantic.
- `InvalidValueError`, a `ValueError` subclass that carries a stable code, so that Pydantic reports it as a field error and the code survives in the error context.
- `StrEnumField`, a generic model field that stores a `StrEnum`, builds its `choices` with `str_enum_to_choices`, returns the enum when Django reads from the database, and supports migrations.
- `BaseModel`, an abstract model with `created_at` and `updated_at`.
- `get_env`, `parse_csv`, `parse_booleanish`, and `str_enum_to_choices`, moved from `rastro_shared_kernel` with their tests.

**Blocked by:** 01 (Settings package and the RASTRO_ prefix)

**Status:** ready-for-agent

- [ ] Pure tests, with no database, show that a `StrValueObject` subclass parses from a JSON string inside a Pydantic model, serializes back to a plain string, and turns an `InvalidValueError` into a Pydantic field error whose context still holds the code.
- [ ] A test shows that a non-string input fails as a type error before the value object runs.
- [ ] A test shows that `StrEnumField` returns the enum member on read, rejects an unknown value, and produces a migration that names the enum.
- [ ] `BaseModel` sets `created_at` on creation and updates `updated_at` on save.
- [ ] The settings import the environment helpers from `rastro.common`, and the moved tests pass there.
- [ ] `rastro_shared_kernel` keeps only what the old `iam` code still imports. Everything that moved is deleted from it.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
