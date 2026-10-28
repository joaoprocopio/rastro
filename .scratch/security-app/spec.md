# Make security the app that holds CSRF, CORS, and the frame headers

Status: ready-for-agent

## Problem Statement

The maintainer's review of PR #4 found three problems in the code that the PR adds:

- The module of `create_app` holds the class of the frame-headers middleware and the constants `CORS_METHODS`, `CORS_HEADERS`, and `FRAME_HEADERS`. The file exists to build the app, so a reader who opens it to see the wiring reads HTTP header policy first. The `rastro` package holds only the wiring, and a class is none of the four forms of code.
- `CorsOrigin` validates an origin with a regular expression of about 15 lines that checks DNS labels, the port range, the default port of each scheme, and IPv6 hosts. No requirement asked for those rules, and the operator who deploys rastro owns a wrong origin.
- CSRF lives in the app `csrf`, while CORS and the frame headers live in the wiring. CORS already reads the CSRF header name from the settings, so the three protections of the browser sit in two places.

## Solution

The app `security` holds CSRF, CORS, and the frame headers, and the app `csrf` goes away. The module of `create_app` imports each piece from `security` and registers it, so the module holds only wiring. The frame-headers middleware becomes a function. `CorsOrigin` becomes a Pydantic URL type in the settings module, beside `PsycopgDsn`, and the regular expression goes away. ADR 0003 is rewritten in place to record the `security` app.

Two HTTP changes are visible to a client:

- A failed CSRF check answers `403` with the problem type `security.csrf_failed`. PR #4 merges into `main` first and answers `csrf.failed`, so a client sees `csrf.failed` become `security.csrf_failed`.
- The route that sets the CSRF cookie moves from `GET /api/v1/csrf` to `GET /api/v1/security/csrf`, and the old path answers `404`.

The CSRF cookie, the CSRF header, the six CSRF settings, `cors_allowed_origins`, the CORS headers, and the frame headers keep their names, values, and defaults.

## User Stories

### Developer of rastro

1. As a developer, I want CSRF, CORS, and the frame headers in one app, so that I find every protection of the browser in one place.
2. As a developer, I want the app label `security`, so that the name says what the app holds without a dictionary.
3. As a developer, I want `GLOSSARY.md` to separate Security from Auth, so that I put a password rule in `auth` and a cross-site rule in `security`.
4. As a developer, I want `CsrfToken` in the domain value objects of `security` with its methods unchanged, so that the move changes no behaviour.
5. As a developer, I want `CsrfFailedError` in the domain errors of `security`, so that every domain error lives in the errors module of its app.
6. As a developer, I want `CsrfFailedError` to keep its class name, so that the code that raises it reads the same.
7. As a developer, I want the error code `security.csrf_failed`, so that the code follows the rule that its prefix is the app label.
8. As a developer, I want the views module of `security` to declare the error-to-status table, so that `create_app` merges it like the table of `auth`.
9. As a developer, I want the CSRF cookie functions and `csrf_check` in the cookie module of `security`, so that CSRF keeps the shape of the Session cookie module of `auth`.
10. As a developer, I want the frame-headers middleware in a `middleware` module of the presentation layer of `security`, so that the module of `create_app` holds only wiring.
11. As a developer, I want the CORS constants in the same `middleware` module, so that every value that `create_app` passes to `add_middleware` sits in one module.
12. As a developer, I want the frame-headers middleware to be a function, so that it follows the rule that everything that is not data, a port, or an adapter is a function.
13. As a developer, I want `create_app` to register each piece of `security` on its own line, so that I see every middleware and dependency of the app in one function.
14. As a developer, I want `create_app` to keep the CSRF check in `FastAPI(dependencies=...)`, so that every route that a router adds gets the check.
15. As a developer, I want only the wiring to import the `security` app, so that no other app depends on it.
16. As a developer, I want the import-linter contract to name the `security` app, so that the rule still holds without a review.
17. As a developer, I want `CorsOrigin` in the settings module, so that a type that only the settings read lives with the settings.
18. As a developer, I want `CorsOrigin` to reuse Pydantic's `HttpUrl`, so that rastro holds no regular expression for a URL.
19. As a developer, I want `CODING_STANDARDS.md` to describe the `security` app, so that the next change copies the current layout.
20. As a developer, I want `CODING_STANDARDS.md` to state that a name is a whole word or a common abbreviation, so that nobody adds a numeronym such as `s6y`.
21. As a developer, I want the layout in `CODING_STANDARDS.md` to list `middleware.py` as a fixed presentation module, so that the next app puts its middleware at the same place.
22. As a developer, I want ADR 0003 to record the `security` app and the options it rejects, so that the next reader knows why CSRF does not live alone.
23. As a developer, I want the comment in the architecture rules that repeats the wiring to go away, so that the comment rule of `CLAUDE.md` holds.
24. As a developer, I want one parametrized test for the frame headers, so that the three requests share one assertion.

### Client of the API

25. As a frontend developer, I want a failed CSRF check to answer `403` with the problem type `security.csrf_failed`, so that I show the right message.
26. As a frontend developer, I want `GET /api/v1/security/csrf` to set the CSRF cookie with the same name, flags, and token size, so that only the path changes.
27. As a frontend developer, I want the preflight from my local origin to keep the CORS headers, the credentials flag, and the CSRF header, so that the frontend keeps working.
28. As a client on an origin outside the list, I want the response to carry no CORS headers, so that the browser blocks my script from reading the response.
29. As a User, I want every response to keep the frame headers, so that no other site shows rastro in a hidden frame.

### Operator

30. As an operator, I want `RASTRO_CORS_ALLOWED_ORIGINS` to keep its name and its empty default, so that no deployment changes its environment.
31. As an operator, I want an origin with no scheme, a scheme other than `http` or `https`, or a port outside the valid range to stop the settings at start, so that a typo of that kind fails before the API answers.
32. As an operator, I want an origin in uppercase or with the default port of its scheme to match the origin that the browser sends, so that I do not have to know how the browser writes an origin.
33. As an operator, I want an origin with a trailing slash or a path to load without an error, so that rastro does not decide for me what a valid origin is, and I own that configuration.
34. As an operator, I want the six CSRF settings to keep their names and defaults, so that no deployment changes its environment.

## Implementation Decisions

### 1. The `security` app

- The app `csrf` becomes the app `security`. It follows the four-layer layout and creates only the modules that it uses: the domain value objects, the domain errors, the presentation cookie module, the presentation `middleware` module, the presentation views, and its tests.
- `CsrfToken` moves to the domain value objects of `security` with `generate`, `matches`, and its `SecretStr` root unchanged.
- `CsrfFailedError` moves to the domain errors of `security`, keeps its class name, and declares the code `security.csrf_failed`.
- `SAFE_METHODS`, `csrf_cookie_set`, and `csrf_check` move to the presentation cookie module of `security`.
- The views module of `security` holds the router, `csrf_set_view` at the path `/csrf`, and `ERROR_STATUSES` with `CsrfFailedError` answering `403`. `create_app` includes the router under `/api/v1/security`, so the view serves `GET /api/v1/security/csrf`.
- `GLOSSARY.md` already holds the Security context: Security controls what another site can make a browser do with rastro, and Auth knows who a person is.

### 2. The middleware module and the wiring

- The presentation `middleware` module of `security` holds `FRAME_HEADERS`, `CORS_METHODS`, `CORS_HEADERS`, and the functions `cors` and `frame_headers`. `cors` receives the ASGI app and the settings and returns the `CORSMiddleware`, so `create_app` registers it with `app.add_middleware(cors, settings=settings)`, and mypy rejects the call without `settings`.
- `frame_headers` receives the ASGI app and returns an ASGI app that adds `FRAME_HEADERS` to the `http.response.start` message of each HTTP request and passes every other scope unchanged. Starlette 1.9 builds a middleware with `cls(app, *args, **kwargs)`, and its `_MiddlewareFactory` protocol accepts a function. A run of the function in a scratch script added both headers to a `200` and a `404`, and `mypy --strict` passed.
- The module of `create_app` imports `csrf_check`, `cors`, `frame_headers`, the router, and `ERROR_STATUSES` from `security`, and registers each one on its own line, as it does today. A function such as `install_security(app, settings)` is rejected, because FastAPI copies the app's dependencies into a route when a router adds it, so a call after an `include_router` leaves that router's routes without the CSRF check and raises no error.
- The module of `create_app` keeps no class, and its only constant is the merged `ERROR_STATUSES`, so `create_app` and the architecture test of the error codes read the same table.

### 3. `CorsOrigin`

- `CorsOrigin` lives in the settings module, beside `PsycopgDsn`, because only the settings parse it and only `create_app` reads it. `TokenBytes` and `SessionLifetime` live in an app because domain code reads them, and `CorsOrigin` has no such reader.
- `CorsOrigin` subclasses Pydantic's `HttpUrl` with its own `UrlConstraints`. This shape comes from a run against Pydantic 2.14.1:

  ```python
  class CorsOrigin(HttpUrl):
      _constraints = UrlConstraints(
          allowed_schemes=["http", "https"], host_required=True, preserve_empty_path=True
      )
  ```

- `preserve_empty_path=True` keeps `http://localhost:5173` with no trailing slash. Without it, Pydantic writes `http://localhost:5173/`, and `CORSMiddleware` matches no browser `Origin`.
- The run showed the behaviour that the operator gets. `HTTP://LOCALHOST:5173` becomes `http://localhost:5173`, and `https://x.com:443` becomes `https://x.com`. `localhost:5173`, `ftp://x.com`, and `http://localhost:99999` fail. `http://localhost:5173/` and `http://localhost:5173/path` load unchanged, and the browser then blocks the frontend.
- `cors` passes `[str(origin) for origin in settings.cors_allowed_origins]` to `CORSMiddleware`.
- The regular expression and the `CorsOrigin` value object in `common` go away.

### 4. Import rules

- The import-linter contract forbids every `rastro` module but `rastro.app` and the `security` app itself to import the `security` app. The settings module imports nothing from `security`.
- The architecture test of the error codes maps `security.csrf_failed` to `403` in place of `csrf.failed`.

### 5. Documents

`CODING_STANDARDS.md` changes in the same commit as the code that it describes:

- The layout section states that a name is a whole word or a common abbreviation, for example `auth` or `csrf`, and never a numeronym such as `s6y`.
- The layout tree lists `middleware.py` in the presentation layer, for the middleware and the constants that `create_app` passes to `add_middleware`.
- The sentences that name the `csrf` app name the `security` app: the `CsrfToken` paragraph, the router paragraph with the route `GET /api/v1/security/csrf`, and the settings paragraph, which places the frame headers and the CORS constants in the `middleware` module of `security`.
- The settings paragraph states that a configuration type that only the settings read, for example `PsycopgDsn` or `CorsOrigin`, lives in the settings module.

ADR 0003 is rewritten in place, with a new file name such as `0003-security-is-an-app-and-create-app-runs-the-csrf-check.md`. The new text records:

- the `security` app with CSRF, CORS, and the frame headers, and the CSRF check in `create_app`
- the rejected option of a `csrf` app alone, because CORS reads the CSRF header name and the CORS and frame-header code now exists
- the rejected option of a module beside `create_app` in the `rastro` package, because the middleware and the header constants are HTTP behaviour and not wiring, and CORS reads the CSRF header name
- the rejected options that ADR 0003 already lists and that still hold: one CSRF module in `common`, CSRF across the fixed modules of `common`, a middleware for the check, and a check on each router
- the consequence that the problem type changes from `csrf.failed` to `security.csrf_failed` and the route moves from `GET /api/v1/csrf` to `GET /api/v1/security/csrf`

PR #4 merges into `main` first with its body unchanged. The body of PR #6, which stacks on PR #4, names the new problem type, the new route, and the risk of an origin with a path.

## Testing Decisions

A good test drives rastro through its interface and asserts what a client or an operator sees. The tests follow the kinds in `CODING_STANDARDS.md`, use no `mock.patch`, and compare the literal JSON of each problem.

- **HTTP through the app that `create_app` builds** is the main seam. The fixtures `client`, `sample_client`, and `cors_client` already build it. The tests assert that:
  - a `POST` with no CSRF header answers `403` with `{"type": "security.csrf_failed", "status": 403}`
  - a `POST` with a matching header passes
  - `GET /api/v1/security/csrf` sets the cookie with the same name, flags, and token size, and `GET /api/v1/csrf` answers `404`
  - a preflight from an allowed origin gets `Access-Control-Allow-Origin` with that origin, `Access-Control-Allow-Credentials: true`, and the CSRF header in `Access-Control-Allow-Headers`
  - an origin written as `CorsOrigin("HTTP://LOCALHOST:5173")` allows a preflight from `http://localhost:5173`
  - a request from an origin outside the list gets no `Access-Control-Allow-Origin`
  - one parametrized test shows that a `2xx` response, a `403` problem, and a `404` problem carry both frame headers
- `frame_headers` gets no unit test, because the HTTP seam shows its behaviour.
- **Settings read from the environment** is the second seam, because a failure at start never reaches HTTP. The tests assert that `localhost:5173`, `ftp://x.com`, and `http://localhost:99999` stop the settings, that `https://x.com:443` loads as `https://x.com`, and that `http://localhost:5173` loads with no trailing slash. Prior art: the settings tests of the token size and of `cors_allowed_origins`.
- The domain tests of `CsrfToken` move to the tests of `security` unchanged.
- The tests of the `CorsOrigin` value object in `common` go away. The settings tests replace them.
- The import-linter contract and the architecture tests stay the checks of structure.

The implementer runs the checks in `README.md` before the work is done.

## Out of Scope

- Validation of an origin beyond what `HttpUrl` checks, for example a rejection of a path or a trailing slash.
- A CORS setting for the methods, the headers, the credentials flag, or `max_age`.
- Other security headers, for example `Strict-Transport-Security` or `X-Content-Type-Options`.
- An observability module. The naming rule applies to it when it exists, so its name is a whole word such as `observability` and not `o11y`.
- A frontend change. The repository holds no frontend.
- The spec and tickets in `.scratch/csrf-app-and-http-headers/`, which stay as the record of the work that PR #4 already holds.

## Further Notes

- Starlette's `ServerErrorMiddleware` sends a `500` from outside every user middleware, so a `500` carries neither the frame headers nor the CORS headers. This behaviour does not change.
- The code review of PR #4 against `main` found the problems that this spec fixes. The maintainer's line comments on PR #4 are on the module of `create_app` and on the `CorsOrigin` regular expression.
