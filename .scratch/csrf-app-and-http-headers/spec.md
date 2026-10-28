# Make CSRF its own app, run its check once, and add the CORS and frame headers

Status: ready-for-agent

## Problem Statement

A review of PR #3 found three problems with CSRF and the HTTP headers of rastro:

- The module that holds all of CSRF in `common` mixes four kinds of code: the `CsrfToken` value object, the `SAFE_METHODS` constant, the cookie functions, and a router with its view. Every other module in rastro holds one kind of code at a fixed place, so a reader who looks for a value object or a view finds CSRF in neither place. Moving each piece to the fixed modules of `common` would make the views module of `common` collect the views of unrelated features.
- Each router declares `dependencies=[Depends(csrf_check)]`. A new app that forgets the line has no CSRF check, and every app imports `csrf_check` from code that it does not own.
- The frontend runs on another port than the API in local development, so the browser blocks every request of the frontend, because rastro sends no CORS headers. In production the frontend and the API share one origin behind a proxy. No response tells the browser that another site may not put a rastro page in a frame.

## Solution

CSRF becomes the app `csrf`, laid out by the rules that every app follows, and it creates only the modules that it uses. `create_app` runs the CSRF check on every route, so no router declares it and no app imports the `csrf` app. The failed check answers `403` with the problem type `csrf.failed`, which follows the app label rule. `create_app` adds the CORS middleware, configured by one setting with the allowed origins, and a middleware that adds the frame headers to each response. ADR 0003 records the decision and the rejected options.

Two HTTP changes are visible to a client:

- A failed CSRF check answers the problem type `csrf.failed`, where it answered `request.csrf_failed`.
- Each response carries `X-Frame-Options: DENY` and `Content-Security-Policy: frame-ancestors 'none'`, and a request from an allowed origin gets the CORS headers.

The route `GET /api/v1/csrf`, the CSRF cookie, the CSRF header, and the six CSRF settings keep their names, flags, and defaults.

## User Stories

### Developer of rastro

1. As a developer, I want CSRF in its own app, so that `common` holds only the code that every app uses and no feature.
2. As a developer, I want `CsrfToken` in the value objects module of the `csrf` app, so that I find it where I find every other value object.
3. As a developer, I want the CSRF cookie functions and `csrf_check` in a cookie module of the `csrf` app, so that CSRF has the same shape as the Session cookie module of `auth`.
4. As a developer, I want the CSRF router and `csrf_set_view` in the views module of the `csrf` app, so that every view lives in a views module.
5. As a developer, I want `CsrfFailedError` in the errors module of the `csrf` app, so that every domain error lives in the errors module of its app.
6. As a developer, I want the `csrf` app to declare its own error-to-status table, so that `create_app` merges it like the table of `auth`.
7. As a developer, I want `CsrfToken` to keep its `generate` and `matches` methods and its `SecretStr` root, so that the move changes no behaviour.
8. As a developer, I want `matches` to keep its comparison of UTF-8 bytes, so that a header with characters outside ASCII still answers `403` and not `500`.
9. As a developer, I want `create_app` to declare the CSRF check once for the whole app, so that a route cannot miss the check.
10. As a developer of a new app, I want my router to need no CSRF line, so that my app is protected without any step.
11. As a developer, I want only the wiring to import the `csrf` app, so that no app depends on another app for CSRF.
12. As a developer, I want an import-linter contract to fail when an app imports the `csrf` app, so that the rule holds without a review.
13. As a developer, I want the sample app's router to drop its CSRF line, so that the reference for a new app shows the new rule.
14. As a developer, I want the router of `auth` to drop its CSRF line, so that `auth` imports nothing from the `csrf` app.
15. As a developer, I want the CSRF check to stay a FastAPI dependency and not a middleware, so that a `CsrfFailedError` reaches the problem handlers and answers `403`.
16. As a developer, I want `CODING_STANDARDS.md` to describe the `csrf` app and the check in `create_app`, so that the next app copies the current pattern.
17. As a developer, I want the CORS and frame headers configured in `create_app`, so that the HTTP server configuration lives with the rest of the wiring.
18. As a developer, I want the frame headers to be constants, so that no setting can turn off a protection that a standard fixes.
19. As a developer, I want the CORS methods, the CORS headers, and the credentials flag to be fixed by the code, so that a wrong setting cannot break the frontend.
20. As a developer, I want the CORS allowed headers to include the CSRF header from its setting, so that a renamed CSRF header still passes the preflight.

### Client of the API

21. As a frontend developer, I want the API to accept requests from my local origin, so that the frontend on its own port can call the API.
22. As a frontend developer, I want the CORS response to allow credentials, so that the browser sends the Session cookie and the CSRF cookie.
23. As a frontend developer, I want the preflight to allow the CSRF header, so that a `POST` with the header reaches the CSRF check.
24. As a frontend developer, I want a failed CSRF check to answer `403` with the problem type `csrf.failed`, so that I show the right message.
25. As a frontend developer, I want `GET /api/v1/csrf` to keep its URL, cookie name, flags, and token size, so that only the problem type of the failure changes.
26. As a client on an origin outside the list, I want the response to carry no CORS headers, so that the browser blocks my script from reading the response.
27. As a User, I want no other site to show a rastro page in a frame, so that a hidden frame cannot trick me into a click.

### Operator

28. As an operator, I want one setting with the allowed CORS origins, so that I allow the local frontend without a code change.
29. As an operator, I want the allowed origins to be empty by default, so that a deployment that forgets the variable allows no other origin.
30. As an operator, I want an invalid origin to stop the settings at start, so that a typo fails before the API answers.
31. As an operator, I want `.env.example` to list the origin of the local frontend, so that local development works with the example environment.
32. As an operator, I want the six CSRF settings to keep their names and defaults, so that no deployment changes its environment.

## Implementation Decisions

### 1. The `csrf` app

- The new app has the label `csrf` and follows the four-layer layout, with only the modules that it uses: the domain value objects, the domain errors, a presentation cookie module, the presentation views, and its tests.
- `CsrfToken` moves to the domain value objects of `csrf` with its methods unchanged.
- `SAFE_METHODS`, `csrf_cookie_set`, and `csrf_check` move to the presentation cookie module of `csrf`, which has the shape of the Session cookie module of `auth`.
- The router and `csrf_set_view` move to the views module of `csrf`. The router has no prefix of its own beyond the app label, so `create_app` includes it under `/api/v1/csrf` and the route stays `GET /api/v1/csrf`.
- `CsrfFailedError` moves to the domain errors of `csrf` with the code `csrf.failed`. The `csrf` views module declares `ERROR_STATUSES` with `CsrfFailedError` answering `403`, and `create_app` merges that table. The common table loses its row.
- The module in `common` that holds CSRF today goes away, and `common` keeps no CSRF code.

### 2. The CSRF check in `create_app`

- `create_app` builds the app with `dependencies=[Depends(csrf_check)]`. FastAPI copies the app's dependencies into each route that a router adds, including a router that a test includes after `create_app` returns.
- No router declares the check. The routers of `auth`, `csrf`, and the sample app drop the line.
- An import-linter contract forbids every `rastro` module but `rastro.app` and the `csrf` app itself to import the `csrf` app. The tests of `csrf` are part of the app.
- The check stays a dependency. A Starlette user middleware runs outside the `ExceptionMiddleware`, so a `CsrfFailedError` raised there reaches the `Exception` handler and answers `500`. ADR 0003 records this.

### 3. CORS

- `create_app` adds Starlette's `CORSMiddleware`.
- A new setting, `cors_allowed_origins`, holds the list of allowed origins, with an empty list as its default. Each origin is a value object with a format rule, per the standard that a configuration value with a rule is a value object: a scheme, a host, an optional port, and no path.
- The code fixes the other values: credentials allowed, the methods `GET` and `POST`, and the headers `Content-Type` and the value of `csrf_header_name`.
- `.env.example` lists the variable with the origin of the local frontend, `http://localhost:5173`.

### 4. Frame headers

- A middleware that `create_app` adds sets `X-Frame-Options: DENY` and `Content-Security-Policy: frame-ancestors 'none'` on each HTTP response. The values are module constants. The middleware only adds headers and never raises.
- The middleware is a pure ASGI middleware in the wiring of the `rastro` package, beside `create_app`, because it configures the HTTP server and belongs to no app.

### 5. Standards

`CODING_STANDARDS.md` changes in the same commit as the code:

- The rule that each router declares the CSRF check becomes the rule that `create_app` declares it once and that only the wiring imports the `csrf` app.
- The sentences that place CSRF in `common` name the `csrf` app.
- "Configure settings" names the CORS origins as a setting and the frame headers as constants.

## Testing Decisions

A good test exercises the module through its interface, HTTP for the app and the value object's methods for the domain, and asserts behaviour that a client sees. The tests follow the kinds in `CODING_STANDARDS.md`, use no `mock.patch`, and compare the literal JSON of each problem.

- **HTTP through the app that `create_app` builds** is the main seam. The `app` and `sample_client` fixtures already build it, and the sample router joins it after `create_app`. The tests assert:
  - a `POST` to a sample route with no CSRF header answers `403` with `{"type": "csrf.failed", "status": 403}`, although the sample router declares no check;
  - a `POST` with a matching header passes;
  - `GET /api/v1/csrf` sets the cookie with the same name, flags, and token size as today;
  - a preflight `OPTIONS` from an allowed origin gets `Access-Control-Allow-Origin` with that origin, `Access-Control-Allow-Credentials: true`, and the CSRF header in `Access-Control-Allow-Headers`;
  - a request from an origin outside the list gets no `Access-Control-Allow-Origin`;
  - a `2xx` response, a `403` problem, and a `404` problem carry both frame headers.
- Prior art: the CSRF tests and the CSRF cookie tests in `common`, which move to the tests of `csrf`, and the settings override through `app.dependency_overrides[app_settings]`.
- **Domain tests** of `CsrfToken` move with it and stay pure, including the comparison of a header with characters outside ASCII.
- **Settings tests** assert the empty default of `cors_allowed_origins`, an origin list that loads, and an invalid origin that stops the settings. Prior art: the token size and SameSite tests. The test that `.env.example` lists every variable covers the new variable.
- **Architecture tests**: the error code table changes `request.csrf_failed` to `csrf.failed` with `403`. The new import-linter contract runs with `uv run lint-imports`.

The implementer runs the checks in `README.md` before the work is done.

## Out of Scope

- A `CurrentUser` dependency, or any route that requires a signed-in User. A later spec decides its shape.
- The deletion of expired Sessions, in `.scratch/ideas/0001-delete-expired-sessions.md`.
- The renewal of a Session while the client uses it, in `.scratch/ideas/0002-renew-the-session-on-use.md`.
- A CORS setting for the methods, the headers, the credentials flag, or `max_age`.
- A frontend change. The repository holds no frontend, and the change of the problem type assumes that no client reads `request.csrf_failed` today.
- Other security headers, for example `Strict-Transport-Security` or `X-Content-Type-Options`.

## Further Notes

- Starlette's `ServerErrorMiddleware` sends the `500` response from outside every user middleware, so a `500` carries neither the frame headers nor the CORS headers. A `500` body is a JSON problem with no content to frame. In local development, the browser reports a `500` from another origin as a CORS error, and the API log still shows the exception.
- `GLOSSARY.md` needs no change, because CSRF, CORS, and the frame headers are no domain terms.
- ADR 0003 records the `csrf` app, the check in `create_app`, and the new problem type.
