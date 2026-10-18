# 03: Output schemas read the model

**What to build:** Let an Output schema read a model directly, so that a new output field is declared once and the view copies no field by hand. The response of every query stays the same. Read the spec (`.scratch/rastro-review-fixes/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start, and follow the auto mode that the spec's Further Notes describe.

An Output schema sets `from_attributes=True`, and its view builds it with `<Output>.model_validate(model)`. A field whose name differs from the model attribute uses `Field(validation_alias=...)`, a nested attribute uses `AliasPath`, and a computed value comes ready from the selector.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `SessionCurrentOutput` reads an Identity with `from_attributes`, and the current Session view builds it with `model_validate`.
- [ ] `GET` on the current Session still answers `200` with exactly `email` and `display_name`.
- [ ] `CODING_STANDARDS.md` states the rule for `from_attributes`, `validation_alias`, `AliasPath`, and computed values.
- [ ] Every decision that the spec did not settle is recorded under `## Comments`, as the spec's Further Notes describe.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
