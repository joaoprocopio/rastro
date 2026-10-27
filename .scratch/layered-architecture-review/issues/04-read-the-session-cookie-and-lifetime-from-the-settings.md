# 04: Read the Session cookie and lifetime from the settings, and hide passwords and Session tokens

**What to build:** An operator sets the Session lifetime and the name, the flags, and the token size of the Session cookie through the settings, with no change to the code. `RawPassword` and `SessionToken` hide their values in `repr`, and `SessionToken.generate` builds every new Session token. Every Session response stays the same under the default settings. Read the spec (`.scratch/layered-architecture-review/spec.md`, sections Secrets, Settings, and How a value reaches the code), `CODING_STANDARDS.md`, the ADRs, and the Decisions of tickets 01 and 02 before you start, and follow the auto mode that the spec's Further Notes describe.

Give `RawPassword` and `SessionToken` a `SecretStr` root, and add `SessionToken.generate(nbytes=...)`. The views of `session/start` and `session/end` read the Session settings from the settings dependency of ticket 01. `session_start` receives the lifetime and the token size as keyword-only arguments, and `Session.start` receives the lifetime. Remove the constants that the settings replace. State in `CODING_STANDARDS.md` that a use case receives a configuration value as a keyword-only argument, beside its ports.

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] Under the default settings, every Session HTTP test passes with an unchanged assertion.
- [ ] An HTTP test that overrides the settings with another cookie name, a lifetime of one hour, `secure=false`, and `samesite=strict` sees `session/start` set the cookie with that name, a `max_age` of `3600`, and those flags, and sees `session/end` delete the cookie with that name.
- [ ] A domain test shows that `Session.start` at 09:00 with a lifetime of one hour sets `expires_at` to 10:00.
- [ ] A use case test with fakes shows that `session_start` stores a Session whose `expires_at` is the clock's time plus the lifetime that it received.
- [ ] A domain test shows that `SessionToken.generate(nbytes=16)` returns a token of 22 characters, and that `repr` of a `SessionToken` and of a `RawPassword` shows `**********`.
- [ ] `RawPassword` still rejects a password shorter than its minimum length.
- [ ] Every check in the README passes.

## Comments
