---
status: accepted
---

# Make security an app, and run the CSRF check once in `create_app`

The app `rastro/security/` holds CSRF, CORS, and the frame headers, and it creates only the modules that it uses. `CsrfToken` sits in `domain/value_objects.py`, `CsrfFailedError` sits in `domain/errors.py` with the code `security.csrf_failed`, the cookie functions and `csrf_check` sit in `presentation/csrf_cookie.py`, the router with `csrf_set_view` sits in `presentation/views.py`, and the CORS constants, the frame headers, and the function `frame_headers` sit in `presentation/middleware.py`. `create_app` declares `FastAPI(dependencies=[Depends(csrf_check)])`, so every route runs the check, no router declares it, and only `rastro/app.py` imports `rastro.security`.

The three protections answer one question: what another site can make a browser do with rastro. CORS allows the CSRF header in a preflight, so it reads the CSRF header name from the settings, and an app for CSRF alone would split one protection across two places. The middleware and the header constants of CORS and the frame headers decide what a response says, so they are HTTP behaviour, and the `rastro` package keeps only the wiring. `create_app` imports each piece of `security` and registers it on its own line.

## Considered options

- **A `csrf` app alone, with CORS and the frame headers in `create_app`.** The app holds only CSRF, but CORS reads the CSRF header name from outside it, and the module of `create_app` holds header policy beside the wiring.
- **A module beside `create_app` in the `rastro` package.** The module holds the CORS constants and the frame headers, but the `rastro` package then holds HTTP behaviour, and CORS still reads the CSRF header name from another place.
- **One `csrf.py` in `common`.** All of CSRF sits in one file, but the file mixes four kinds of code, and the layout section of `CODING_STANDARDS.md` needs an exception for it.
- **CSRF across the fixed modules of `common`.** Each kind sits at its fixed place, as in `auth`, but `common` then holds a feature, and its `views.py` collects the views of every feature without an owner.
- **A function such as `install_security(app, settings)`.** FastAPI copies the dependencies of the app into a route when a router adds it, so a call after an `include_router` leaves the routes of that router without the CSRF check, and nothing raises an error.
- **A middleware for the check.** Starlette runs a user middleware outside the `ExceptionMiddleware`, so a `CsrfFailedError` raised there skips the `BaseError` handler and reaches the `Exception` handler, which answers `500`. The middleware would have to build its own `403` problem, outside `rastro.common.presentation.problems`.
- **A check on each router.** A new app that forgets the line has no CSRF check, and each app imports `csrf_check` from another app.

## Consequences

- The problem type of a failed check changes from `csrf.failed` to `security.csrf_failed`, so a client that reads the old code breaks.
- The route that sets the CSRF cookie moves from `GET /api/v1/csrf` to `GET /api/v1/security/csrf`, and the old path answers `404`.
- A route that must skip the check needs its own decision, because the check covers every route of the app.
