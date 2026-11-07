---
status: accepted
---

# Write the Session and the rehashed User in one transaction

`session_start` adds the new `Session` and, when the User's hash has outdated parameters, updates the `User` with a new hash, both inside the one transaction that the request opens. This writes two aggregates in one transaction on purpose. The reason is Vernon's user-aggregate affinity: only a sign-in and a password reset of one User change its hash, so the shared transaction competes only with those two requests of that User.

Fowler and Evans say that a transaction does not cross an aggregate boundary, and Vernon calls one aggregate per transaction a rule of thumb with named exceptions. The rehash fits his exceptions because the cleartext password exists only during the sign-in request: argon2-cffi recommends a rehash after each successful authentication for that reason. A later step cannot hash a password that it never receives.

## Serialize a sign-in with a password reset

`password_reset_confirm` writes the hash of the same `User`, so `session_start` holds a row lock on the `User` from its read until its commit. With no lock, a Postgres test showed two outcomes when a confirmation committed after the read of a sign-in. The Session of the sign-in survived the reset, and with an outdated hash, the rehash of the old password replaced the new hash, so only the old password worked.

With the lock, a confirmation that runs first makes the old password fail, because the locked read waits for the commit and returns the new hash. A confirmation that runs second waits at its `UPDATE` of the `User`, so its `DELETE` of each Session also removes the new Session. The confirmation takes no lock of its own, so it hashes the new password with no lock held.

The lock mode is `FOR NO KEY UPDATE`. A Postgres 18 test rejected the other three modes:

- **`FOR KEY SHARE`** does not conflict with the `UPDATE` of a confirmation, so the two use cases do not serialize.
- **`FOR SHARE`** lets two sign-ins read together. With an outdated hash, each `UPDATE` of a rehash then waits for the other sign-in, and Postgres aborts one with a deadlock error, so its request answers `500`.
- **`FOR UPDATE`** blocks the `FOR KEY SHARE` of a foreign key check, so the job that stores a Reset token of this User would wait for the sign-in.

## Write three aggregates in the confirmation

`password_reset_confirm` removes the Reset token, stores the new hash of the `User`, and removes every `Session` of the User in one transaction, as spec #20 decides. A split could spend the link and keep the old password, or store the new password and keep a stolen Session alive. A failure in the one transaction leaves all three as they were, so the link still works.

## Considered options

- **An eventual rehash.** The request starts the Session, and a task updates the hash afterwards. The task needs the cleartext password in its message, so the password would cross the broker, which keeps no queue and would lose the rehash when the worker is down. This adds a task and a failure mode for a hash that the next sign-in replaces anyway.
- **No rehash.** `session_start` writes only the Session, so a hash keeps the argon2 parameters of the day the User registered.

## Consequences

- When the update of the `User` fails, the Session does not start, and the request answers `500`. A sign-in never leaves a Session with a half-written rehash, or a rehash without its Session.
- A future split of `session_start` into two transactions needs a new reason that outweighs the cleartext constraint above, and a new ADR.
- A sign-in holds the row lock during the argon2 verify, which took about 65 ms with the default parameters on one development machine, and a wrong password holds it too. A person who knows an email address can therefore delay the sign-ins and the confirmation of that User, and no other User waits for this lock.
- Each request that waits for the lock holds its database connection, so parallel sign-ins of one email address can take every connection of the pool of a process, and requests of other Users then wait for a connection.
- Only a known email address takes the lock. Parallel sign-ins of a known address can then answer more slowly than those of an unknown address, which gives a time measurement a signal about who has a User.
