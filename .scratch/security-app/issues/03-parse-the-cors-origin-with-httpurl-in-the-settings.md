# 03: Parse the CORS origin with HttpUrl in the settings

**What to build:** An operator writes an allowed CORS origin, and rastro checks it only as far as Pydantic's `HttpUrl` does. `CorsOrigin` moves to the settings module, beside `PsycopgDsn`, as a subclass of `HttpUrl` with its own `UrlConstraints`. The shape below comes from a run against Pydantic 2.14.1, and `preserve_empty_path=True` keeps the origin without a trailing slash, so `CORSMiddleware` matches the `Origin` that the browser sends:

```python
class CorsOrigin(HttpUrl):
    _constraints = UrlConstraints(
        allowed_schemes=["http", "https"], host_required=True, preserve_empty_path=True
    )
```

`create_app` passes `str(origin)` for each origin to `CORSMiddleware`. The regular expression and the `CorsOrigin` value object in `common` go away, with their tests. `CODING_STANDARDS.md` states that a configuration type that only the settings read, for example `PsycopgDsn` or `CorsOrigin`, lives in the settings module. The body of PR #6 names the risk of an origin with a path. Read the spec (`.scratch/security-app/spec.md`, section "3. `CorsOrigin`") before you start.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Given `localhost:5173`, `ftp://x.com`, or `http://localhost:99999` in `RASTRO_CORS_ALLOWED_ORIGINS`, then the settings fail to load.
- [x] Given `https://x.com:443`, then the settings load it as `https://x.com`.
- [x] Given `http://localhost:5173`, then the settings load it with no trailing slash.
- [x] Given `http://localhost:5173/path`, then the settings load it unchanged.
- [x] Given the origin `CorsOrigin("HTTP://LOCALHOST:5173")`, then a preflight from `http://localhost:5173` gets `Access-Control-Allow-Origin: http://localhost:5173`.
- [x] Given `RASTRO_CORS_ALLOWED_ORIGINS` unset, then the settings load an empty list.
- [x] No regular expression for an origin remains in rastro.
- [x] The checks in `README.md` pass.

## Comments

PR #4 merges into `main` first with its body unchanged, and the body of PR #6 names the risk of an origin with a path.
