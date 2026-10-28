# 03: Make the Session cookie expire with the Session

**What to build:** A client signs in, and the browser drops the Session cookie at the same moment the server stops accepting the Session. `session_start` returns a new `SessionStartOutput` with the `SessionToken` and `expires_at`. The view passes it to the Session cookie module, which sets `Expires` to `expires_at`, sets no `Max-Age`, and no longer reads `session_lifetime`. `POST /api/v1/auth/session/start` still answers `204` with no body. Read the spec (`.scratch/architecture-deepening/spec.md`, section "3. The Session cookie takes its expiry from the Session"), `CODING_STANDARDS.md`, and ADR 0002 before you start.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Given a User with correct Credentials, when the client starts a Session, then the response is `204` with no body, and the cookie's `Expires` equals the `expires_at` of the stored Session.
- [ ] Given settings with a Session lifetime of 1 hour, when the client starts a Session, then the cookie's `Expires` is 1 hour after the start, and the cookie keeps the name and flags from the settings.
- [ ] A use case test asserts that `session_start` returns a `SessionStartOutput` whose `expires_at` equals the clock's time plus the lifetime.
- [ ] The Session cookie module reads no lifetime setting.
- [ ] The checks in `README.md` pass.
