# 01: Make security the app that holds CSRF

**What to build:** A developer finds CSRF in the app `security`, and the app `csrf` no longer exists. `CsrfToken`, `CsrfFailedError`, the cookie functions with `csrf_check`, and the router with `csrf_set_view` and `ERROR_STATUSES` move to the same layers and modules of `security`, with their behaviour unchanged. `CsrfFailedError` keeps its class name and declares the code `security.csrf_failed`. `create_app` includes the router of `security` under `/api/v1/security`, so the view serves `GET /api/v1/security/csrf`, and it keeps the CSRF check in `FastAPI(dependencies=...)`. The import-linter contract forbids every `rastro` module but `rastro.app` and `security` itself to import `security`, and the architecture test of the error codes maps `security.csrf_failed` to `403`. The comment in the architecture rules that repeats what `create_app` does goes away. `CODING_STANDARDS.md` states that a name is a whole word or a common abbreviation and never a numeronym, and its sentences that name the `csrf` app name `security`. ADR 0003 is rewritten in place with a new file name, and records the decision and the rejected options that the spec lists. The body of PR #6 names the new problem type and route. Read the spec (`.scratch/security-app/spec.md`, sections "1. The `security` app", "4. Import rules", and "5. Documents") before you start.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Given a `POST` to a sample route with no CSRF header, then it answers `403` with `{"type": "security.csrf_failed", "status": 403}`.
- [x] Given a `POST` with a header that matches the CSRF cookie, then it passes.
- [x] Given `GET /api/v1/security/csrf`, then it sets the CSRF cookie with the same name, flags, and token size as before.
- [x] Given `GET /api/v1/csrf`, then it answers `404`.
- [x] Given a module in `auth` that imports `security`, then `uv run lint-imports` fails.
- [x] No module, test, or document outside `.scratch/` names the app `csrf` or the code `csrf.failed`.
- [x] `CODING_STANDARDS.md` holds the naming rule, and ADR 0003 describes the `security` app.
- [x] The checks in `README.md` pass.

## Comments

- PR #4 merges into `main` first with its body unchanged, and the body of PR #6 names the new problem type and route.
- ADR 0003 names a `csrf` app only as a rejected option, and `test_csrf_set.py` names `GET /api/v1/csrf` only to assert that it answers `404`.
