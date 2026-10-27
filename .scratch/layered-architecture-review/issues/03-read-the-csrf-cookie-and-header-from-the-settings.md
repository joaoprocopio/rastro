# 03: Read the CSRF cookie and header from the settings, with a `CsrfToken`

**What to build:** An operator sets the name, the flags, and the token size of the CSRF cookie and the name of the CSRF header through the settings, with no change to the code. A `CsrfToken` value object holds each CSRF token and hides it in `repr`. Every CSRF response stays the same under the default settings. Read the spec (`.scratch/layered-architecture-review/spec.md`, sections Settings, How a value reaches the code, and CSRF token), `CODING_STANDARDS.md`, the ADRs, and the Decisions of ticket 01 before you start, and follow the auto mode that the spec's Further Notes describe.

Add `CsrfToken` to the common domain's `value_objects` module, with `generate(nbytes=...)`, a `SecretStr` root, and no format rule. `csrf_check` and the code that sets the CSRF cookie read their values from the settings dependency of ticket 01. State in `CODING_STANDARDS.md` that a setting holds every value an operator may change, and which value objects hide their value.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Under the default settings, every CSRF HTTP test passes with an unchanged assertion.
- [ ] An HTTP test that overrides the settings with another cookie name, another header name, `secure=false`, `httponly=true`, and `samesite=strict` sees `GET /api/v1/auth/csrf` set the cookie with that name and those flags, and a `POST` that sends the token in that header passes the check.
- [ ] A request with a malformed or missing CSRF header answers `{"type": "request.csrf_failed", "status": 403}`.
- [ ] A domain test shows that `CsrfToken.generate(nbytes=16)` returns a token of 22 characters, and that `repr` of a `CsrfToken` shows `**********`.
- [ ] Every check in the README passes.

## Comments
