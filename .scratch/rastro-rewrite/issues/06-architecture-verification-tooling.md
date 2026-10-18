# 06: Tooling that checks the architecture

**What to build:** Add the tools that check the rules in `CODING_STANDARDS.md`, so that an agent or a maintainer learns about a layer violation from a failing check and not from a review. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The tools are:

- import-linter, with contracts for the modules that exist after ticket 05, for example the rule that `values` imports no Django. The spec's "Tooling" section lists the full set of contracts. This ticket adds the contracts whose modules exist, and each later ticket adds the contracts for the modules it creates.
- Architecture tests in pytest. They inspect every public function in the services and selectors modules of every app, and they fail when one of these holds:
  - an argument is not keyword-only or has no type;
  - an argument is a raw `str` or `dict`, except the `request` of a Session;
  - a dependency argument has a default;
  - a service returns something other than `None`;
  - a name does not follow `<entity>_<action>`.

  The same tests fail when any rastro code calls `full_clean()`, `clean_fields()`, `validate_unique()`, or `validate_constraints()`, or when a model defines `clean()`.

**Blocked by:** 05 (The Identity model and the iam value objects)

**Status:** done

- [x] `lint-imports` runs from the project configuration and passes.
- [x] A deliberate import of Django into a values module makes `lint-imports` fail. The test or the check that proves this is not left in the code.
- [x] The architecture tests pass while no services or selectors module exists, and fail on a sample service that breaks each rule above. The samples live in the tests, not in an app.
- [x] The architecture tests fail on a call to `full_clean()` or one of its siblings, and on a model that defines `clean()`.
- [x] The Checks section of `README.md` lists `lint-imports`.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket-06`, before the merge of `rastro-rewrite`:

- `pyproject.toml` holds `[tool.importlinter]` with two contracts: `iam layers` keeps `values` as its own layer below `models`, and `values import no framework` forbids `django`, `pydantic`, and `pydantic_core` in every `rastro.*.values`, with the two Pydantic imports of `rastro.common.values` ignored because that module is the Pydantic adapter. `uv run lint-imports` reports 2 kept, 0 broken.
- A temporary `from django.db import models` and `from rastro.iam import models` in `src/rastro/iam/values.py` broke both contracts, and the report named the two lines. I reverted the file; the proof is not in the code.
- `tests/architecture/rules.py` holds the checkers, and the sample tests build their modules inside the tests. `test_services_and_selectors.py` scans every `services.py`, `selectors.py`, `services/`, and `selectors/` of every app under `src/rastro/`, passes while none exists, and one sample per rule fails: a positional argument, an argument without a type, a raw `str` and a raw `dict`, an `HttpRequest` under a name other than `request`, a dependency with a default, a service that returns data, a function without a return type, and a name without `<entity>_<action>`. A temporary `services.py` and a `selectors/` package in `iam` with a broken function each failed the real test with six violations.
- The spec gives `identity_get_current` a `request`, so the name of the function cannot tell a Session function apart. The test allows an `HttpRequest` only under the argument name `request`.
- import-linter rejects `django.conf` as a forbidden module, so `test_no_service_or_selector_imports_django_conf` scans the imports of those modules instead, and `CODING_STANDARDS.md` says so in the import-linter bullet.
- `test_validation.py` scans every Python file under `src/rastro/` for `full_clean()`, `clean_fields()`, `validate_unique()`, `validate_constraints()`, and a class that defines `clean()`. A temporary `clean()` that called `full_clean()` in `Identity` failed the real test with two violations.
- `test_values.py` keeps every app's `values.py` on the standard library and `rastro.common.values`, which import-linter cannot express because it has no allow list for the standard library.
- The gate: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest` (108 passed) are green. `docker compose build django` builds the image. I did not run `docker compose up --build`, because the ports belong to the main directory; the merger runs the full stack.
- Contracts that wait for their modules, for tickets 07 to 10: the rows `apis` and `services : selectors` above `models` in `iam layers`; `only apis import schemas` (source `rastro.iam.*`, forbidden `rastro.iam.schemas`, ignore `rastro.iam.apis -> rastro.iam.schemas`); `services and selectors import no pydantic` (forbidden `pydantic`); `services and selectors never import adapters`; and `only deps imports adapters` (ignore `rastro.iam.deps -> rastro.iam.adapters`). import-linter fails on a module that does not exist, so each ticket adds the contract with the module.
