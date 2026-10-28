# 04: Block frames with headers on each response

**What to build:** A User cannot see a rastro page inside a frame of another site. A pure ASGI middleware in the wiring of the `rastro` package, beside `create_app`, adds `X-Frame-Options: DENY` and `Content-Security-Policy: frame-ancestors 'none'` to each HTTP response. The values are module constants, because a standard fixes them, and the middleware only adds headers and never raises. A `500` carries no frame header, because Starlette's `ServerErrorMiddleware` sends it from outside every user middleware. `CODING_STANDARDS.md` names the frame headers as constants in "Configure settings". Read the spec (`.scratch/csrf-app-and-http-headers/spec.md`, section "4. Frame headers", and "Further Notes") before you start.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Given a `2xx` response, then it carries `X-Frame-Options: DENY` and `Content-Security-Policy: frame-ancestors 'none'`.
- [x] Given a `403` problem from the CSRF check and a `404` problem, then each carries both headers.
- [x] The checks in `README.md` pass.
