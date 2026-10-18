# 01: Rename apis to views and name every URL

**What to build:** Rename every view module and view function to the Django convention, and give every URL a name inside its app namespace, so that later tickets and tests build URLs with `reverse()`. The HTTP contract stays the same for every caller. Read the spec (`.scratch/rastro-review-fixes/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start, and follow the auto mode that the spec's Further Notes describe.

Each app's view module is `views.py`, and each view function is `<entity>_<action>_view`. The shared helpers `parse_body`, `respond`, `require_POST`, and `require_GET` move from `rastro.common`'s API module into its views module, and the API module is deleted. Each app URLconf sets `app_name`, and each URL pattern has a name.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] No module named `apis` remains in `rastro`, and every view function ends in `_view`.
- [ ] The shared view helpers live in `rastro.common`'s views module beside the CSRF failure view and the handlers.
- [ ] `reverse("iam:<name>")` resolves every `iam` URL, and every URL, method, status, and body is unchanged.
- [ ] The import-linter contracts and the architecture tests name `views` in place of `apis`, and the `iam` test package for views is named after views.
- [ ] `CODING_STANDARDS.md` describes views, their names, and the URL names as the code does them.
- [ ] Every decision that the spec did not settle is recorded under `## Comments`, as the spec's Further Notes describe.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
