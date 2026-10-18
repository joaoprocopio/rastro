# 11: Remove the old architecture and update the docs

**What to build:** Delete what remains of the DDD architecture and make the docs describe the new pattern, so that a developer who copies rastro finds one pattern, the same one in the code and in the docs. Read the spec (`.scratch/rastro-rewrite/PRD.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

After tickets 08 and 10, no endpoint uses the old layers. This ticket deletes them and completes the checks:

- the `domain`, `application`, `infrastructure`, `presentation`, and `shared` subpackages of `iam`;
- the rest of `rastro_base` and `rastro_shared_kernel`;
- the `model_bakery` dependency and the old fixtures in the root `conftest.py`, which factories replace.

**Blocked by:** 02 (Telemetry without personal data), 08 (Identity registration), 10 (Current Session, end of Session, and the CSRF cookie)

**Status:** ready-for-agent

- [ ] The old `iam` subpackages, `rastro_base`, and `rastro_shared_kernel` no longer exist, and nothing imports them.
- [ ] `model_bakery` is no longer a dependency, and every test builds its data with factory_boy factories.
- [ ] The import-linter contracts match the full list in the spec's "Tooling" section, and they pass.
- [ ] The `rastro` package holds only the settings package, the root URLconf, the WSGI and ASGI entry points, and the telemetry setup.
- [ ] The README describes the new architecture, the HTTP contract, and the check gate, and no longer describes DDD layers.
- [ ] The project `CLAUDE.md` no longer says "structured with DDD" and describes the new pattern in one line.
- [ ] `CODING_STANDARDS.md` no longer says that some code predates the rewrite.
- [ ] A final HTTP run covers the five operations of the spec's HTTP contract from end to end.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
