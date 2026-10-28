# 02: Run the CSRF check once in `create_app`

**What to build:** A developer of a new app gets the CSRF check on every route without a line in the router, and no app imports the `csrf` app. `create_app` builds the app with `dependencies=[Depends(csrf_check)]`, so FastAPI copies the check into each route that a router adds, including a router that a test includes after `create_app` returns. The routers of `auth`, `csrf`, and the sample app drop their CSRF line. An import-linter contract forbids every `rastro` module but `rastro.app` and the `csrf` app itself to import the `csrf` app. The check stays a FastAPI dependency, because a Starlette user middleware runs outside the `ExceptionMiddleware` and its `CsrfFailedError` would answer `500`. `CODING_STANDARDS.md` replaces the rule that each router declares the check with the rule that `create_app` declares it once. Read the spec (`.scratch/csrf-app-and-http-headers/spec.md`, section "2. The CSRF check in `create_app`") and ADR 0003 before you start.

**Blocked by:** 01 (Move CSRF into the `csrf` app)

**Status:** resolved

- [x] Given the sample router with no CSRF line, when a client sends a `POST` to a sample route with no CSRF header, then the response is `{"type": "csrf.failed", "status": 403}`.
- [x] Given a matching CSRF cookie and header, when a client sends a `POST` to a sample route, then the CSRF check lets it through.
- [x] No router in `auth`, `csrf`, or the sample app declares `csrf_check`.
- [x] Given a module in `auth` that imports the `csrf` app, then `uv run lint-imports` fails, and without that import it passes.
- [x] The checks in `README.md` pass.
