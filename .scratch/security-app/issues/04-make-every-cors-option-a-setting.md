# 04: Make every option of the CORS middleware a setting

**Blocked by:** None (tickets 01 to 03 are on the branch `security-app`, PR #6)

**Status:** resolved

## Problem

An operator who deploys rastro behind a frontend that sends a `DELETE` request, reads a response header, or needs a longer preflight cache must change the code. Today the operator sets only `RASTRO_CORS_ALLOWED_ORIGINS`. The function `cors` in `src/rastro/security/presentation/middleware.py` fixes everything else: the methods `CORS_METHODS = ["GET", "POST"]`, the headers `CORS_HEADERS = ["Content-Type"]` plus `settings.csrf_header_name`, the credentials flag `True`, and Starlette's defaults for the rest. The maintainer wants every option that Starlette's `CORSMiddleware` accepts as a setting, with the option list of django-cors-headers 4.9.0 as the model. A wrong value is the operator's responsibility, so rastro checks a value only as far as its type does.

This ticket replaces the bullet "A CORS setting for the methods, the headers, the credentials flag, or `max_age`" in the "Out of Scope" section of `.scratch/security-app/spec.md`.

## Solution

`Settings` in `src/rastro/settings.py` gets seven settings beside `cors_allowed_origins`, and `cors` passes each one to `CORSMiddleware` with no other value:

| Setting | Type | Default | Argument of `CORSMiddleware` |
|---|---|---|---|
| `RASTRO_CORS_ALLOWED_ORIGIN_REGEX` | `str \| None` | `None` | `allow_origin_regex` |
| `RASTRO_CORS_ALLOW_METHODS` | `list[HTTPMethod \| Literal["*"]]` | `DELETE, GET, OPTIONS, PATCH, POST, PUT` | `allow_methods` |
| `RASTRO_CORS_ALLOW_HEADERS` | `list[str]` | `accept, authorization, content-type, user-agent, x-csrftoken, x-csrf-token, x-requested-with` | `allow_headers` |
| `RASTRO_CORS_EXPOSE_HEADERS` | `list[str]` | `[]` | `expose_headers` |
| `RASTRO_CORS_PREFLIGHT_MAX_AGE` | `timedelta` (ISO 8601, like `RASTRO_SESSION_LIFETIME`) | `PT10M` | `max_age`, in whole seconds |
| `RASTRO_CORS_ALLOW_CREDENTIALS` | `bool` | `true` | `allow_credentials` |
| `RASTRO_CORS_ALLOW_PRIVATE_NETWORK` | `bool` | `false` | `allow_private_network` |

`HTTPMethod` is the enum of the `http` module of the standard library. The defaults of the methods and the headers are the defaults of django-cors-headers, plus `x-csrf-token`, which matches the default `RASTRO_CSRF_HEADER_NAME=X-CSRF-Token`. The default of the max age and of the credentials flag keep today's behaviour.

Deliverables:

1. The seven settings, each with its default and a line in `.env.example`.
2. `cors` reads only the settings. `CORS_METHODS` and `CORS_HEADERS` go away, and `cors` no longer adds `settings.csrf_header_name` to the headers.
3. `CODING_STANDARDS.md`, section "Configure settings": the rule "A value that a standard fixes stays a constant" drops the example "the CORS methods and headers that the frontend needs", and the sentence about the `middleware` module names only the frame headers as its constant.
4. ADR 0003 (`docs/adr/0003-security-is-an-app-and-create-app-runs-the-csrf-check.md`) drops every reason that rests on CORS reading the CSRF header name: the sentence "CORS allows the CSRF header in a preflight, so it reads the CSRF header name from the settings, and an app for CSRF alone would split one protection across two places", and the same reason in the first two considered options. The reason that stays is that the three protections answer one question: what another site can make a browser do with rastro. The first paragraph names the frame headers, `cors`, and `frame_headers` in `presentation/middleware.py`, with no CORS constants.
5. `.scratch/security-app/spec.md`: the "Out of Scope" bullet above goes away, and section 2 no longer names `CORS_METHODS` and `CORS_HEADERS`.

## Edge cases

- **Wildcard in methods or headers**: `["*"]` reaches Starlette unchanged. Starlette then allows its eight known methods, or mirrors every header that the browser requests.
- **Wildcard in origins**: stays rejected, because `CorsOrigin` is an `HttpUrl`. Every authenticated route reads the Session cookie, and Starlette with `"*"` and credentials answers any origin.
- **A changed CSRF header name**: an operator who sets `RASTRO_CSRF_HEADER_NAME=X-Other` and keeps the default headers gets a failed preflight for every `POST`. The operator keeps both settings in step.
- **A typo in a method**, for example `PSOT`: the settings fail to load.
- **A regex that is too wide**, for example `https://.*.example.com`, which accepts `https://evil-example.com`: rastro loads it. Starlette applies `fullmatch`.
- **A negative or fractional max age**: rastro passes the whole seconds of the `timedelta` and adds no rule.
- **Mixed case in headers**: Starlette adds `Accept`, `Accept-Language`, `Content-Language`, and `Content-Type` to every list, so `Access-Control-Allow-Headers` can list `accept` and `Accept`. The browser compares headers without case.

## Out of scope

- An option to allow every origin, `CORS_ALLOW_ALL_ORIGINS` in django-cors-headers.
- A regex that limits which routes get the CORS headers, `CORS_URLS_REGEX` in django-cors-headers. Starlette has no such argument.
- Validation beyond the type of each setting.

## Acceptance criteria

Tests drive the app that `create_app` builds through HTTP, or load `Settings` from the environment, as the tests in `src/rastro/tests/test_app.py` and `src/rastro/tests/test_settings.py` do.

- [x] Given no `RASTRO_CORS_*` variable but the origins, when the settings load, then each of the seven settings holds the default in the table.
- [x] Given the default settings and an allowed origin, when the browser sends a preflight for `DELETE` with the header `X-CSRF-Token`, then the response allows the origin, lists `DELETE, GET, OPTIONS, PATCH, POST, PUT` in `Access-Control-Allow-Methods`, allows `x-csrf-token`, and carries `Access-Control-Allow-Credentials: true` and `Access-Control-Max-Age: 600`.
- [x] Given `RASTRO_CSRF_HEADER_NAME=X-Other` and the default headers, when the browser sends a preflight with the header `X-Other`, then the response does not allow the header.
- [x] Given the regex `https://[a-z]+\.example\.com`, when `https://app.example.com` sends a preflight, then the response allows the origin. When `https://example.org` sends one, then the response carries no `Access-Control-Allow-Origin`.
- [x] Given the methods `["*"]` and the headers `["*"]`, when the browser sends a preflight for `HEAD` with the header `X-Anything`, then the response allows both.
- [x] Given the methods `["PSOT"]`, then the settings fail to load.
- [x] Given the expose headers `["X-Request-Id"]`, when an allowed origin sends a `GET`, then the response carries `Access-Control-Expose-Headers: X-Request-Id`.
- [x] Given the max age `PT1H`, when the browser sends a preflight, then the response carries `Access-Control-Max-Age: 3600`.
- [x] Given the credentials flag `false`, when an allowed origin sends a preflight, then the response carries no `Access-Control-Allow-Credentials`.
- [x] Given the private network flag `true`, when the browser sends a preflight with `Access-Control-Request-Private-Network: true`, then the response carries `Access-Control-Allow-Private-Network: true`.
- [x] `src/rastro/security/presentation/middleware.py` defines no CORS constant, and the checks in `README.md` pass.

The maintainer changed the regex setting from a list to one `str | None`, `RASTRO_CORS_ALLOWED_ORIGIN_REGEX`, because Starlette takes one regex. The first version joined the list as `(?:a)|(?:b)`, so a regex with a global inline flag such as `(?i)` loaded in the settings and then failed Starlette's `re.compile` at start. An operator who needs two patterns writes `a|b`, and an invalid regex fails when the app starts.
