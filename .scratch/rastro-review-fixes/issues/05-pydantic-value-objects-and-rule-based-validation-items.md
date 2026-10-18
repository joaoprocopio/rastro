# 05: Pydantic value objects and rule-based validation items

**What to build:** Turn every value object into a frozen Pydantic `RootModel` with declarative rules, and report each validation item by the rule that failed, with its limit. A frontend can tell "too long" from "wrong format" on the same field and show "at least 8 characters" without a copy of the rule. Read the spec (`.scratch/rastro-review-fixes/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start, and follow the auto mode that the spec's Further Notes describe.

The value object base in `rastro.common` holds only `frozen=True`, and code reads a value through `.root`. The `iam` value objects keep their current rules, written with `StringConstraints` and a `BeforeValidator` for NFKC. `StrValueObject`, `__get_pydantic_core_schema__`, `parse_value_object`, `InvalidValueError`, and every `iam.invalid_*` code are deleted. The problems module translates `string_too_short`, `string_too_long`, and `string_pattern_mismatch`, and the fields module holds a model field and a form field for value objects that pass a failure through `to_error`. The spec's value object section holds a declaration from the prototype.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] Every `iam` value object is a frozen `RootModel` with its current normalization and limits, and the value object tests cover normalization and rejection with no database.
- [ ] mypy rejects a raw `str` and the wrong value object in a service argument.
- [ ] A registration with an invalid email and a 5-character password answers `422` with an `invalid_format` item at `#/email` and a `too_short` item at `#/password` that carries `"min_length": 8`.
- [ ] A value longer than its limit answers a `too_long` item that carries `max_length`, and no item exposes the email pattern.
- [ ] A missing field, a wrong type, malformed JSON, and an unknown field keep their current item types.
- [ ] The admin shows `request.invalid_format` on the email field and `request.too_short` on the password field, and stores nothing.
- [ ] `createsuperuser` and the Identity manager parse with `model_validate` and keep the registration rules.
- [ ] A value from the database that fails its value object still raises.
- [ ] No code mentions `StrValueObject`, `parse_value_object`, `InvalidValueError`, or `iam.invalid_`.
- [ ] The import contract for `values` allows `pydantic`, `services` and `selectors` still import no `pydantic`, and a pytest architecture test rejects `pydantic.ValidationError` or `pydantic_core` outside the problems module and the fields module.
- [ ] `CODING_STANDARDS.md` describes value objects, validation items, and the architecture checks as the code does them.
- [ ] Every decision that the spec did not settle is recorded under `## Comments`, as the spec's Further Notes describe.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
