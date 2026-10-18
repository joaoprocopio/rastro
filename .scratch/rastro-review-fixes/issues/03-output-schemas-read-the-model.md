# 03: Output schemas read the model

**What to build:** Let an Output schema read a model directly, so that a new output field is declared once and the view copies no field by hand. The response of every query stays the same. Read the spec (`.scratch/rastro-review-fixes/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start, and follow the auto mode that the spec's Further Notes describe.

An Output schema sets `from_attributes=True`, and its view builds it with `<Output>.model_validate(model)`. A field whose name differs from the model attribute uses `Field(validation_alias=...)`, a nested attribute uses `AliasPath`, and a computed value comes ready from the selector.

**Blocked by:** 01

**Status:** ready-for-agent

- [x] `SessionCurrentOutput` reads an Identity with `from_attributes`, and the current Session view builds it with `model_validate`.
- [x] `GET` on the current Session still answers `200` with exactly `email` and `display_name`.
- [x] `CODING_STANDARDS.md` states the rule for `from_attributes`, `validation_alias`, `AliasPath`, and computed values.
- [x] Every decision that the spec did not settle is recorded under `## Comments`, as the spec's Further Notes describe.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket/03-output-schemas`. `SessionCurrentOutput` sets `from_attributes=True`, and `session_current_view` builds it with `SessionCurrentOutput.model_validate(identity)`. `src/rastro/iam/tests/views/test_session_current.py` passes unchanged, so `GET` on the current Session still answers `200` with exactly `email` and `display_name`. The gate is green: `ruff check`, `ruff format --check`, `mypy`, `lint-imports` (6 kept), `pytest` (167 passed), and `manage.py check`. I did not run `docker compose up --build`; the merger runs it.

### Decisions

- **Gap**: the spec states the Output rule but no check that keeps it. **Chosen**: `tests/architecture/test_schemas.py` fails when an `*Output` schema in an app's `schemas.py` does not set `from_attributes`, and when a `views` module calls an `*Output` class, because a constructor call is how a view copies fields by hand. `CODING_STANDARDS.md` lists the check. **Rejected**: an import-linter contract, which cannot inspect a class config or a call, and no check, which leaves the rule to review.
- **Gap**: the spec does not say where `from_attributes=True` lives. **Chosen**: each Output schema sets its own `model_config`, as each Input schema sets `extra="forbid"`. **Rejected**: a shared `Output` base class in `rastro.common`, which adds a module for one config line and hides the config from the reader of `schemas.py`.
- **Gap**: no Output field today differs from its model attribute, reads a related model, or holds a computed value. **Chosen**: `CODING_STANDARDS.md` states the rules for `validation_alias`, `AliasPath`, and computed values with examples, and it adds that `alias` is wrong because it also renames the JSON member. **Rejected**: a new field in `SessionCurrentOutput` to show the rule, which changes the HTTP contract, and a sample schema in `rastro.common.tests`, which tests Pydantic and not rastro.
