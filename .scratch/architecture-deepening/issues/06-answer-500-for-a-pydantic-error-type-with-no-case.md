# 06: Answer 500 for a Pydantic error type with no case

**What to build:** A developer adds a validation rule whose Pydantic error type has no case, and the view test for that rule fails with a `500`, before a deploy. Today the rule answers `request.invalid_type` with no warning. The `case _` branch of the problems module raises a built-in exception whose message names the Pydantic error type. Each Pydantic type error that rastro's DTOs and value objects raise today gets an explicit case that answers `request.invalid_type`, for example `int_parsing` for `"coats": "two"`. Find the list from the field types of every DTO and value object. The sample app's paint route may need a new field to raise a type with no case. Read the spec (`.scratch/architecture-deepening/spec.md`, section "6. Every Pydantic error type has an explicit case"), `CODING_STANDARDS.md` (sections "Raise in place of a fallback value" and "Return errors as problem details"), and the ADRs before you start.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Given a paint body with `"coats": "two"`, when the client sends it, then the item for `#/coats` has the type `request.invalid_type`, as today.
- [ ] Given a body that raises a Pydantic error type with no case, when the client sends it, then the response is the `500` problem, and the body shows no input value.
- [ ] Every validation view test that passed before this ticket passes with the same JSON.
- [ ] The checks in `README.md` pass.
