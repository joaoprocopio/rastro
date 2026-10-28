# 04: Let a client end an expired Session

**What to build:** A client whose Session has expired signs out, and the response is `204`, the browser loses the Session cookie, and the row leaves the database. Today the client gets `401`, and the cookie and the row stay. `session_end` deletes the Session that the token finds, whether or not the Session is active. With no token, or with a token that no Session holds, it still raises `NotAuthenticatedError`. `session_get` keeps its rule: an expired Session is not authenticated. Read the spec (`.scratch/architecture-deepening/spec.md`, section "4. Ending an expired Session succeeds"), `GLOSSARY.md`, and `CODING_STANDARDS.md` before you start.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Given a Session past its expiry, when the client ends it, then the response is `204`, the Session cookie is cleared, and no Session row remains. This test replaces the test that asserts `401` and one row.
- [x] Given no Session cookie, when the client ends a Session, then the response is the `auth.not_authenticated` problem with status `401`.
- [x] Given a Session token that no Session holds, when the client ends a Session, then the response is the `auth.not_authenticated` problem with status `401`.
- [x] Given a Session past its expiry, when the client reads its Session, then the response is still `401`.
- [x] The checks in `README.md` pass.
