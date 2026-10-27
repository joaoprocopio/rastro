---
status: accepted
---

# Write the Session and the rehashed User in one transaction

`session_start` adds the new `Session` and, when the User's hash has outdated parameters, updates the `User` with a new hash, both inside the one transaction that the request opens. This writes two aggregates in one transaction on purpose. The reason is Vernon's user-aggregate affinity: only the User who signs in changes their own hash, and only at that moment, so no other request competes for the same `User` and the shared transaction costs no contention.

Fowler and Evans say that a transaction does not cross an aggregate boundary, and Vernon calls one aggregate per transaction a rule of thumb with named exceptions. The rehash fits his exceptions because the cleartext password exists only during the sign-in request: argon2-cffi recommends a rehash after each successful authentication for that reason. A later step cannot hash a password that it never receives.

## Considered options

- **An eventual rehash.** The request starts the Session, and a task updates the hash afterwards. The task needs the cleartext password in its message, so the password would cross the broker, which keeps no queue and would lose the rehash when the worker is down. This adds a task and a failure mode for a hash that the next sign-in replaces anyway.
- **No rehash.** `session_start` writes only the Session, so a hash keeps the argon2 parameters of the day the User registered.

## Consequences

- When the update of the `User` fails, the Session does not start, and the request answers `500`. A sign-in never leaves a Session with a half-written rehash, or a rehash without its Session.
- A future split of `session_start` into two transactions needs a new reason that outweighs the cleartext constraint above, and a new ADR.
