# 05: Move CSRF into one common module with its own route

**What to build:** A developer reads and changes CSRF in one common presentation module, and a new app uses CSRF without a dependency on `auth`. The module holds `CsrfToken` (with `generate`, `matches`, and its `SecretStr` root), `SAFE_METHODS`, `csrf_check`, the CSRF cookie, and an `APIRouter` with the route that sets the cookie. It follows the shape of the Session cookie module. `CsrfToken` leaves the common domain. The route moves from `/api/v1/auth/csrf` to `/api/v1/csrf`, and `create_app` includes the common router. `CsrfFailedError` stays in the common presentation errors with its status row, and every router keeps `dependencies=[Depends(csrf_check)]`. The module that holds `csrf_check` and `csrf_cookie_set` today goes away. Read the spec (`.scratch/architecture-deepening/spec.md`, section "5. One CSRF module in the common presentation"), `CODING_STANDARDS.md`, and the ADRs before you start.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] When a client calls `GET /api/v1/csrf`, then the response is `204` and sets the CSRF cookie with the name, flags, and token size from the settings.
- [x] When a client calls `GET /api/v1/auth/csrf`, then the response is the `404` problem.
- [x] Given the token from the new route in the cookie and the header, when the client sends a `POST` to an auth route, then the CSRF check lets it through. Without the header, the response is the `request.csrf_failed` problem with status `403`.
- [x] No module in a domain package declares `CsrfToken`, and the CSRF view tests live in `common`.
- [x] The checks in `README.md` pass.
