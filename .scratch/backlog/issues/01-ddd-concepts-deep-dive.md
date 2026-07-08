# Go deeper into the DDD building blocks

Status: ready-for-human
Type: task

The project is structured around DDD tactical patterns, but several concepts are used
loosely. Study each one properly and reconcile the codebase with the intended meaning —
note gaps or misuses as follow-up issues where found.

## Concepts

- [ ] **Shared kernel** — the shared model/code two contexts agree to co-own. Clarify what
  actually belongs in `rastro_shared_kernel/` vs `rastro_base/` (the latter looks like generic
  framework scaffolding, not a domain-shared kernel). Decide the boundary and document it.
- [ ] **Anti-corruption layer** — a translation layer protecting the domain from an external
  model. Identify where one is needed (e.g. between infrastructure/services and the domain) and
  whether the current mappers already play this role.
- [ ] **Conformist** — the relationship where a downstream context simply adopts the upstream
  model. Note where this applies (if anywhere) so it's an explicit choice, not an accident.
- [ ] **Aggregate** — consistency boundary with a single root. Review `conta/domain/aggregates.py`:
  is the invariant enforcement inside the root, and are value objects held correctly?
- [ ] **Domain event** — something meaningful that happened in the domain. Currently absent;
  decide whether the `conta` flows (e.g. account entry) should raise them.
- [ ] **Specification pattern** — encapsulated, composable business rules. Evaluate whether any
  current validation (email/password constraints in `conta/domain/value_objects.py`) would be
  clearer as specifications.

## Notes

- When conclusions land, capture domain terms in `CONTEXT.md` and decisions as ADRs under
  `docs/adr/` (see `docs/agents/domain.md`).
