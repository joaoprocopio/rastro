# 01: Move CSRF into the `csrf` app

**What to build:** A developer finds each piece of CSRF at the fixed place of its kind, in the new app `csrf`, and `common` holds no CSRF code. `CsrfToken` moves to the domain value objects of `csrf` with `generate`, `matches`, and its `SecretStr` root unchanged. `CsrfFailedError` moves to the domain errors of `csrf` with the code `csrf.failed`, and the `csrf` views module declares its `ERROR_STATUSES` table, which `create_app` merges. `SAFE_METHODS`, `csrf_cookie_set`, and `csrf_check` move to a presentation cookie module with the shape of the Session cookie module of `auth`. The router and `csrf_set_view` move to the `csrf` views module, and the route stays `GET /api/v1/csrf`. The routers of `auth` and the sample app keep their CSRF line in this ticket, and import `csrf_check` from the `csrf` app until ticket 02. `CODING_STANDARDS.md` names the `csrf` app in place of the common module. Read the spec (`.scratch/csrf-app-and-http-headers/spec.md`, section "1. The `csrf` app"), ADR 0003, and `CODING_STANDARDS.md` before you start.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] When a client calls `GET /api/v1/csrf`, then the response is `204` and sets the CSRF cookie with the name, flags, and token size from the settings.
- [ ] Given a `POST` to an auth route or a sample route with no CSRF header, then the response is `{"type": "csrf.failed", "status": 403}` with `application/problem+json`.
- [ ] Given a header with characters outside ASCII, then the response is the `403` problem and not `500`.
- [ ] The architecture test of error codes lists `csrf.failed` with `403`, and no longer lists `request.csrf_failed`.
- [ ] No module in `common` declares or imports CSRF code, and the CSRF tests live in the tests of `csrf`.
- [ ] The checks in `README.md` pass.
