# 02: Move the frame headers and the CORS constants into security

**What to build:** A developer who opens the module of `create_app` reads only wiring. The presentation `middleware` module of `security` holds `FRAME_HEADERS`, `CORS_METHODS`, `CORS_HEADERS`, and `frame_headers`. `frame_headers` is a function that receives the ASGI app and returns an ASGI app, which adds `FRAME_HEADERS` to the start message of each HTTP response and passes every other scope unchanged. The module of `create_app` imports these names from `security`, registers each one on its own line, and keeps no class and no constant but the merged `ERROR_STATUSES`. The HTTP behaviour does not change. The layout tree in `CODING_STANDARDS.md` lists `middleware.py` in the presentation layer, and the settings paragraph places the frame headers and the CORS constants in that module. The three tests that assert the frame headers become one parametrized test. Read the spec (`.scratch/security-app/spec.md`, sections "2. The middleware module and the wiring" and "5. Documents") before you start.

**Blocked by:** 01 (Make security the app that holds CSRF)

**Status:** resolved

- [x] Given a `2xx` response, a `403` problem from the CSRF check, and a `404` problem, then one parametrized test shows that each carries `X-Frame-Options: DENY` and `Content-Security-Policy: frame-ancestors 'none'`.
- [x] Given a preflight from an allowed origin, then it still gets `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials: true`, and the CSRF header in `Access-Control-Allow-Headers`.
- [x] The module of `create_app` defines no class, and its only constant is the merged `ERROR_STATUSES`.
- [x] `CODING_STANDARDS.md` lists `middleware.py` in the layout tree.
- [x] The checks in `README.md` pass.

## Comments

The third criterion stays unticked. The module of `create_app` defines no class and no header constant, but it keeps `ERROR_STATUSES`, the merged error-to-status table. `CODING_STANDARDS.md` states that `rastro/app.py` merges the tables, and the root `conftest.py` and `tests/architecture/test_error_codes.py` import the merged table, so the move of `ERROR_STATUSES` needs its own decision.

The maintainer kept `ERROR_STATUSES` in `rastro/app.py`, because each app declares its table, the wiring imports each table by name, and the architecture test reads the same table that `create_app` installs.

The maintainer moved the construction of `CORSMiddleware` into a function `cors` in the `middleware` module, so `create_app` registers it with `app.add_middleware(cors, settings=settings)` and imports no CORS constant.
