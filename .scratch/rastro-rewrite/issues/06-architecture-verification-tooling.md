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

**Status:** ready-for-agent

- [ ] `lint-imports` runs from the project configuration and passes.
- [ ] A deliberate import of Django into a values module makes `lint-imports` fail. The test or the check that proves this is not left in the code.
- [ ] The architecture tests pass while no services or selectors module exists, and fail on a sample service that breaks each rule above. The samples live in the tests, not in an app.
- [ ] The architecture tests fail on a call to `full_clean()` or one of its siblings, and on a model that defines `clean()`.
- [ ] The Checks section of `README.md` lists `lint-imports`.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
