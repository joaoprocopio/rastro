# 04: Read the Session cookie and lifetime from the settings, and hide passwords and Session tokens

**What to build:** An operator sets the Session lifetime and the name, the flags, and the token size of the Session cookie through the settings, with no change to the code. `RawPassword` and `SessionToken` hide their values in `repr`, and `SessionToken.generate` builds every new Session token. Every Session response stays the same under the default settings. Read the spec (`.scratch/layered-architecture-review/spec.md`, sections Secrets, Settings, and How a value reaches the code), `CODING_STANDARDS.md`, the ADRs, and the Decisions of tickets 01 and 02 before you start, and follow the auto mode that the spec's Further Notes describe.

Give `RawPassword` and `SessionToken` a `SecretStr` root, and add `SessionToken.generate(nbytes=...)`. The views of `session/start` and `session/end` read the Session settings from the settings dependency of ticket 01. `session_start` receives the lifetime and the token size as keyword-only arguments, and `Session.start` receives the lifetime. Remove the constants that the settings replace. State in `CODING_STANDARDS.md` that a use case receives a configuration value as a keyword-only argument, beside its ports.

**Blocked by:** 01, 02

**Status:** resolved

- [x] Under the default settings, every Session HTTP test passes with an unchanged assertion.
- [x] An HTTP test that overrides the settings with another cookie name, a lifetime of one hour, `secure=false`, and `samesite=strict` sees `session/start` set the cookie with that name, a `max_age` of `3600`, and those flags, and sees `session/end` delete the cookie with that name.
- [x] A domain test shows that `Session.start` at 09:00 with a lifetime of one hour sets `expires_at` to 10:00.
- [x] A use case test with fakes shows that `session_start` stores a Session whose `expires_at` is the clock's time plus the lifetime that it received.
- [x] A domain test shows that `SessionToken.generate(nbytes=16)` returns a token of 22 characters, and that `repr` of a `SessionToken` and of a `RawPassword` shows `**********`.
- [x] `RawPassword` still rejects a password shorter than its minimum length.
- [x] Every check in the README passes.

## Comments

### Decisions

- **Gap: the names of the configuration arguments of `session_start`.** Chosen: `lifetime: timedelta` and `token_bytes: int`, after the ports. `Session.start` takes `lifetime` too, so one name follows the value from the view to the aggregate. Rejected: `session_lifetime` and `session_token_bytes`, which repeat the Session in a use case that only starts Sessions; `nbytes`, which reads as a size of anything in the use case's signature.
- **Gap: how a test builds a `RawPassword` or a `SessionToken`.** mypy types the constructor of a `RootModel` with its root type, so `RawPassword("password")` fails mypy once the root is a `SecretStr`. Chosen: a test that needs a value writes `RawPassword(SecretStr("password"))`, and a value object test that checks the parsing of raw text calls `RawPassword.model_validate("1234567")`, as an edge does. Rejected: a `type: ignore` at each call; an `__init__` on the value object that accepts a `str`, which breaks the shape of every other `RootValueObject`.
- **Gap: where the HTTP tests change the Session cookie settings.** Chosen: the `other_session_cookie` fixture in `rastro/auth/tests/views/conftest.py` overrides `app_settings` with a copy of the settings that changes the name, the lifetime, and all three flags, `httponly=false` included. The `session/end` test moves the cookie of `signed_in_client` to the new name, so a `204` also shows that `CurrentSessionToken` reads the cookie by the name of the settings. Rejected: an override inside each test, because two tests need the same state and `CODING_STANDARDS.md` then asks for a fixture.
- **Gap: where `signed_in_client` reads the cookie name, the token size, and the lifetime.** Chosen: from the root `settings` fixture, and the `SESSION_COOKIE` constant goes away with the other constants. Rejected: a test-only constant, which would let the fixture and the settings drift apart.
- **Gap: `CODING_STANDARDS.md` said that a use case receives a configuration value through a port.** The spec's rule contradicts that sentence. Chosen: the section on use cases states the keyword-only rule, and the section on adapters says that adapters, dependencies, and views read `Settings` and points at it. The section on Sessions names the settings in place of the removed constants. Rejected: a new port that returns the Session settings, which the spec rules out. Ticket 03 wrote the paragraph in "Write value objects" on which value objects hide their value, and this ticket adds `RawPassword` and `SessionToken` to it, the hash as a place that reads the secret, and the `SecretStr(...)` form of a test.

