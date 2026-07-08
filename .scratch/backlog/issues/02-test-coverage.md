# Finish the test suite

Status: ready-for-agent
Type: task

Complete unit/integration coverage for every module that still lacks tests. Tests live next
to their target in a `__tests__/` package and run with `uv run pytest`.

## Remaining modules

- [ ] **`shared_kernel::value_objects`** — `src/rastro_shared_kernel/value_objects.py`. Cover
      construction, validation, and equality of each value object.
- [ ] **`iam::application::use_cases`** — `src/rastro/iam/application/use_cases.py`. Test each
      use case's happy path and error paths with fakes/stubs for injected dependencies.
- [ ] **`iam::application::dtos::LoginInput`** — `src/rastro/iam/application/dtos.py`. Test
      validation of the login input DTO (accepted/rejected shapes).
- [ ] **`iam::presentation::views`** — `src/rastro/iam/presentation/views.py`. Integration
      tests through Django's test client: status codes, error responses, wiring.
- [ ] **`iam::infrastructure::repositories`** — `src/rastro/iam/infrastructure/repositories.py`.
      Test persistence/lookup against the DB (or a fake), plus not-found behavior.
- [ ] **`iam::infrastructure::services`** — `src/rastro/iam/infrastructure/services.py`. Test
      service behavior (e.g. password hashing/verification) in isolation.
- [ ] **`iam::domain::aggregates`** — `src/rastro/iam/domain/aggregates.py`. Test invariant
      enforcement and aggregate construction.
- [ ] **`iam::domain::value_objects`** — `src/rastro/iam/domain/value_objects.py`. Cover
      `Email`, `DisplayName`, `RawPassword`, `HashedPassword`.
  - Regression: `RawPassword` already sets `strip_whitespace=False` — assert that leading/trailing
    whitespace in a password is preserved (never stripped), so this never silently regresses.
- [ ] **`iam::models`** — `src/rastro/iam/models.py`. Test the Django ORM model(s):
      fields, constraints, and any mapping to/from domain objects.

## Notes

- Reference existing tests for the house style: `rastro_base/__tests__/`,
  `rastro_shared_kernel/__tests__/`, `iam/shared/__tests__/`.
- `ready-for-agent`, but the `RawPassword` whitespace behavior is a deliberate design choice —
  don't "fix" it to strip.
