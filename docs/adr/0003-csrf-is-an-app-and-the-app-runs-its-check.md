---
status: accepted
---

# Make CSRF its own app, and run its check once in `create_app`

CSRF moves out of `common` into the app `rastro/csrf/`, which creates only the modules that it uses: `CsrfToken` in `domain/value_objects.py`, `CsrfFailedError` in `domain/errors.py` with the code `csrf.failed`, the cookie functions and `csrf_check` in `presentation/csrf_cookie.py`, and the router with `csrf_set_view` in `presentation/views.py`. `create_app` declares `FastAPI(dependencies=[Depends(csrf_check)])`, so every route runs the check, no router declares it, and only `rastro/app.py` imports `rastro.csrf`.

A single `common/presentation/csrf.py` held a value object, a constant, the cookie functions, a router, and a view. Every other module in rastro holds one kind of code at a fixed place, so that file was the one module organised by topic. Splitting CSRF across the fixed modules of `common` fixed the kinds, but it made `common/presentation/views.py` hold the views of unrelated features. CSRF has no use case and no table, but as its own app it follows the layout rules that already exist, and its router under `/api/v1/<app label>/` serves `GET /api/v1/csrf`.

## Considered options

- **One `csrf.py` in `common`.** All of CSRF sits in one file, but the file mixes four kinds of code, and the layout section of `CODING_STANDARDS.md` needs an exception for it.
- **CSRF across the fixed modules of `common`.** Each kind sits at its fixed place, as in `auth`, but `common` then holds a feature, and its `views.py` collects the views of every feature without an owner.
- **A wider app such as `rastro/security/`, with CORS and the frame headers.** CORS and the frame headers only configure the HTTP server, so they are wiring in `create_app`, and the wider name would describe code that does not exist.
- **A middleware for the check.** Starlette runs a user middleware outside the `ExceptionMiddleware`, so a `CsrfFailedError` raised there skips the `BaseError` handler and reaches the `Exception` handler, which answers `500`. The middleware would have to build its own `403` problem, outside `rastro.common.presentation.problems`.
- **A check on each router.** A new app that forgets the line has no CSRF check, and each app imports `csrf_check` from another app.

## Consequences

- The problem type of a failed check changes from `request.csrf_failed` to `csrf.failed`, so a client that reads the old code breaks.
- A route that must skip the check needs its own decision, because the check now covers every route of the app.
