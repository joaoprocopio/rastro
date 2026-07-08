# Finish the test suite

Status: ready-for-agent
Type: task

Complete unit/integration coverage for every module that still lacks tests. Tests live next
to their target in a `__tests__/` package and run with `uv run pytest`.

## Remaining modules

- [ ] **`shared_kernel::value_objects`** — `src/rastro_shared_kernel/value_objects.py`. Cover
  construction, validation, and equality of each value object.
- [ ] **`conta::application::use_cases`** — `src/rastro/conta/application/use_cases.py`. Test each
  use case's happy path and error paths with fakes/stubs for injected dependencies.
- [ ] **`conta::application::dtos::EntrarInput`** — `src/rastro/conta/application/dtos.py`. Test
  validation of the login input DTO (accepted/rejected shapes).
- [ ] **`conta::presentation::views`** — `src/rastro/conta/presentation/views.py`. Integration
  tests through Django's test client: status codes, ProblemDetail error responses, wiring.
- [ ] **`conta::infrastructure::repositories`** — `src/rastro/conta/infrastructure/repositories.py`.
  Test persistence/lookup against the DB (or a fake), plus not-found behavior.
- [ ] **`conta::infrastructure::services`** — `src/rastro/conta/infrastructure/services.py`. Test
  service behavior (e.g. password hashing/verification) in isolation.
- [ ] **`conta::domain::aggregates`** — `src/rastro/conta/domain/aggregates.py`. Test invariant
  enforcement and aggregate construction.
- [ ] **`conta::domain::value_objects`** — `src/rastro/conta/domain/value_objects.py`. Cover
  `Email`, `DisplayName`, `RawPassword`, `HashedPassword`.
  - Regression: `RawPassword` already sets `strip_whitespace=False` — assert that leading/trailing
    whitespace in a password is preserved (never stripped), so this never silently regresses.
- [ ] **`conta::models`** — `src/rastro/conta/models.py`. Test the Django ORM model(s):
  fields, constraints, and any mapping to/from domain objects.

## Notes

- Reference existing tests for the house style: `rastro_base/__tests__/`,
  `rastro_shared_kernel/__tests__/`, `conta/shared/__tests__/`.
- `ready-for-agent`, but the `RawPassword` whitespace behavior is a deliberate design choice —
  don't "fix" it to strip.
