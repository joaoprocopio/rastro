# 03: Read the CSRF cookie and header from the settings, with a `CsrfToken`

**What to build:** An operator sets the name, the flags, and the token size of the CSRF cookie and the name of the CSRF header through the settings, with no change to the code. A `CsrfToken` value object holds each CSRF token and hides it in `repr`. Every CSRF response stays the same under the default settings. Read the spec (`.scratch/layered-architecture-review/spec.md`, sections Settings, How a value reaches the code, and CSRF token), `CODING_STANDARDS.md`, the ADRs, and the Decisions of ticket 01 before you start, and follow the auto mode that the spec's Further Notes describe.

Add `CsrfToken` to the common domain's `value_objects` module, with `generate(nbytes=...)`, a `SecretStr` root, and no format rule. `csrf_check` and the code that sets the CSRF cookie read their values from the settings dependency of ticket 01. State in `CODING_STANDARDS.md` that a setting holds every value an operator may change, and which value objects hide their value.

**Blocked by:** 01

**Status:** ready-for-agent

- [x] Under the default settings, every CSRF HTTP test passes with an unchanged assertion.
- [x] An HTTP test that overrides the settings with another cookie name, another header name, `secure=false`, `httponly=true`, and `samesite=strict` sees `GET /api/v1/auth/csrf` set the cookie with that name and those flags, and a `POST` that sends the token in that header passes the check.
- [x] A request with a malformed or missing CSRF header answers `{"type": "request.csrf_failed", "status": 403}`.
- [x] A domain test shows that `CsrfToken.generate(nbytes=16)` returns a token of 22 characters, and that `repr` of a `CsrfToken` shows `**********`.
- [ ] Every check in the README passes.

## Comments

### Decisions

- **Gap: how a test names the CSRF cookie and header once the constants `CSRF_COOKIE` and `CSRF_HEADER` go away.** Chosen: the `client`, `sample_client`, and `signed_in_client` fixtures read `settings.csrf_cookie_name` and `settings.csrf_header_name`, so they follow the settings of the app. A test function names the default as a literal, `"rastro_csrf"` or `"X-CSRF-Token"`, because the literal is the contract that a client reads, as `test_the_csrf_cookie_is_readable_by_scripts` already asserts `rastro_csrf=`. Rejected: keeping the constants beside the settings, which would hold each default twice; a `settings` argument on every CSRF test, which adds a fixture to read a fixed default.
- **Gap: the signature of `csrf_cookie_set`.** Chosen: `csrf_cookie_set(response, *, settings: Settings)`, and `csrf_set_view` passes its `AppSettings`. Rejected: a dependency that sets the cookie, because a view that sets a cookie calls `set_cookie` on its `response` argument.
- **Gap: the parse in `csrf_check`.** Chosen: `csrf_check` keeps its checks of an absent or empty cookie and an absent header on the raw text, then parses both into `CsrfToken` and compares the bytes of the secret values with `secrets.compare_digest`. A header outside ASCII still answers `403`. Rejected: parsing an absent value into an empty `CsrfToken`, which hides the "absent" case in the value object.
- **Gap: where `CODING_STANDARDS.md` states which value objects hide their value.** Chosen: a paragraph in "Write value objects" that names `CsrfToken`, keeps `Email`, `DisplayName`, and the hashes plain, and states the rule for a new secret. Ticket 04 adds `RawPassword` and `SessionToken` to it. The rule that a setting holds every value that an operator may change sits in "Configure settings", and "Reject cross-site requests with a CSRF token" names the settings and the defaults. Rejected: a new section, which would split the value object rules.
- **Unmet in this run: "every check in the README passes".** The agent ran `ruff check`, `ruff format --check`, `mypy`, and `lint-imports` on the whole repo, and `pytest` on `src/rastro/common/tests` and `src/rastro/auth/tests/views` only, as the caller asked. The full `pytest` run is left to the integration branch.
