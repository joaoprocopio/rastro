# Backlog

Migrated from the old root `TODO.md`. This is the standing backlog for `rastro` — an
experimental Django + DDD project for exercising OpenTelemetry and the Grafana stack.

Two tracks of open work remain, tracked as issues under `issues/`:

- `01-ddd-concepts-deep-dive.md` — study the DDD building blocks the codebase leans on.
- `02-test-coverage.md` — finish the test suite (single task covering every remaining module).

## Done (kept for history)

Project refactors already completed:

- Base errors `raise` and are handled globally; trivially JSON-serializable (code, title, details).
- Cleaner approach for mappers (`rastro_base/mapper.py`, `iam/shared/mappers.py`).
- `str_strip_whitespace` lives on the base pydantic model (`rastro_base/pydantic.py`); inherited models rely on it.
- Proper dependency injection with factories for use cases (`iam/infrastructure/composition.py`).
- Remaining endpoints converted into use cases.

Tests already written: `rastro_base::error`, `rastro_base::problem`, `shared_kernel::env`,
`shared_kernel::utils`, `iam::shared::mappers`, `rastro::codes`, `rastro::middleware`.
