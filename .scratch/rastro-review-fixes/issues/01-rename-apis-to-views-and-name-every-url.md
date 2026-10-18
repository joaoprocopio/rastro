# 01: Rename apis to views and name every URL

**What to build:** Rename every view module and view function to the Django convention, and give every URL a name inside its app namespace, so that later tickets and tests build URLs with `reverse()`. The HTTP contract stays the same for every caller. Read the spec (`.scratch/rastro-review-fixes/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start, and follow the auto mode that the spec's Further Notes describe.

Each app's view module is `views.py`, and each view function is `<entity>_<action>_view`. The shared helpers `parse_body`, `respond`, `require_POST`, and `require_GET` move from `rastro.common`'s API module into its views module, and the API module is deleted. Each app URLconf sets `app_name`, and each URL pattern has a name.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] No module named `apis` remains in `rastro`, and every view function ends in `_view`.
- [x] The shared view helpers live in `rastro.common`'s views module beside the CSRF failure view and the handlers.
- [x] `reverse("iam:<name>")` resolves every `iam` URL, and every URL, method, status, and body is unchanged.
- [x] The import-linter contracts and the architecture tests name `views` in place of `apis`, and the `iam` test package for views is named after views.
- [x] `CODING_STANDARDS.md` describes views, their names, and the URL names as the code does them.
- [x] Every decision that the spec did not settle is recorded under `## Comments`, as the spec's Further Notes describe.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket/01-views`. `src/rastro/iam/tests/views/test_urls.py` checks `reverse()` against the literal path of every `iam` URL, and the existing HTTP tests still pass unchanged, so every URL, method, status, and body stays the same. The gate is green: `ruff check`, `ruff format --check`, `mypy`, `lint-imports` (6 kept), `pytest` (163 passed), and `manage.py check`. I did not run `docker compose up --build`; the merger runs it.

### Decisions

- **Gap**: the spec moves `parse_body`, `respond`, `require_POST`, and `require_GET` into `rastro.common.views`, but the API module also held `problem_response`, `problem_type`, and `PROBLEM_MEDIA_TYPE`. **Chosen**: a new `rastro.common.problems` module holds the three, because the middleware imports them and `rastro.common.views` imports the middleware. Ticket 04 grows this module into the problems module of the spec. **Rejected**: moving them into `rastro.common.views`, which creates an import cycle with the middleware, and keeping `rastro.common.apis` for them, which the ticket deletes.
- **Gap**: the spec names view functions `<entity>_<action>_view`, but not the Django hooks in `rastro.common.views`. **Chosen**: `csrf_failure_view`, `not_found_view`, and `server_error_view`, with `CSRF_FAILURE_VIEW`, `handler404`, and `handler500` updated, so every view function ends in `_view`. **Rejected**: keeping `csrf_failure`, `not_found`, and `server_error` as exceptions to the rule.
- **Gap**: the spec gives one URL name, `session_start`, and no rule. **Chosen**: the URL name is the view name without `_view`: `identity_register`, `session_current`, `session_start`, `session_end`, and `csrf_get`. **Rejected**: names derived from the path, such as `session` for `GET /session`, which say nothing about the operation.
- **Gap**: no check keeps the view and URL rules after this ticket. **Chosen**: `tests/architecture/test_views.py` walks the root URLconf and fails when a URL with a view in `rastro` has no name or no namespace, or when a view or error handler is not a `<entity>_<action>_view` function in a `views` module. `CODING_STANDARDS.md` lists the check. **Rejected**: an import-linter contract, which cannot inspect names or URL patterns, and no check, which leaves the rule to review.
- **Gap**: the sample app in `rastro.common.tests.sample` is a test URLconf, where Django ignores `app_name`. **Chosen**: its module is `views.py` with `paint_apply_view`, `paint_count_view`, and `boom_raise_view`, and its `urls.py` wraps the named patterns in `include((sample_patterns, "sample"))`, so `reverse("sample:paint_apply")` resolves at the same paths. **Rejected**: `app_name` in the sample URLconf, which Django ignores in a root URLconf, and unnamed sample URLs, which break the rule for the tests of ticket 02.
- **Gap**: `rastro.common.tests` had `test_apis.py` for the helpers and `test_views.py` for the hooks, and both now test `rastro.common.views`. **Chosen**: one `test_views.py` that runs every test against the sample URLconf. The `404` test now resolves `/nope` through the sample URLconf, which re-exports the same `handler404`. **Rejected**: a second test module for one source module.
- **Gap**: the gate failed before this ticket. Commit `fe09e81` locked ruff 0.17.1, whose wider default rule set reports 34 findings in code that predates it. **Chosen**: `pyproject.toml` pins `select = ["E4", "E7", "E9", "F"]`, the pre-0.17 defaults, in a separate commit. **Rejected**: fixing the 34 findings here, which rewrites generics in `fields.py` that ticket 05 replaces and adds `ClassVar` to Django `Meta` attributes, and leaving the gate red for every ticket. The user decides whether to adopt the new rules in a change of its own.
