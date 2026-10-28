# 03: Accept the origin of the local frontend with CORS

**What to build:** A frontend developer runs the frontend on its own port, and the browser lets it call the API with the Session cookie and the CSRF header. `create_app` adds Starlette's `CORSMiddleware`. A new setting, `cors_allowed_origins`, holds the allowed origins with an empty list as its default, so a deployment that forgets the variable allows no other origin. Each origin is a value object with a format rule: a scheme, a host, an optional port, and no path. The code fixes the other values: credentials allowed, the methods `GET` and `POST`, and the headers `Content-Type` and the value of `csrf_header_name`. `.env.example` lists the variable with `http://localhost:5173`. `CODING_STANDARDS.md` names the CORS origins as a setting in "Configure settings". Read the spec (`.scratch/csrf-app-and-http-headers/spec.md`, section "3. CORS") before you start.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Given an allowed origin, when the browser sends a preflight `OPTIONS`, then the response has `Access-Control-Allow-Origin` with that origin, `Access-Control-Allow-Credentials: true`, and the CSRF header in `Access-Control-Allow-Headers`.
- [x] Given a CSRF header renamed through the settings, then the preflight allows the new header name.
- [x] Given an origin outside the list, when it sends a request, then the response has no `Access-Control-Allow-Origin`.
- [x] Given no variable, then `cors_allowed_origins` is empty.
- [x] Given an origin with a path or with no scheme, then the settings fail to load.
- [x] The checks in `README.md` pass.
