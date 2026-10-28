# Delete each Session whose lifetime has run out

Status: needs-triage
Type: feature

## Problem

A User signs in from a browser and never ends the Session. The Session's lifetime runs out, but its row stays in `auth_session` forever, because no code deletes an expired Session. Each sign-in adds one row, so the table grows with every Session that a client abandons.

A planned change makes `session_end` delete an expired Session when the client still presents its Session token. That change does not cover a Session that no client ends.

## Solution

A taskiq task deletes every Session whose `expires_at` is in the past. The task follows the task rules in `CODING_STANDARDS.md`: it opens its own transaction, builds its repository with the `dependencies` factories, and calls one use case. The use case reads the time from the `Clock` port.

Deliverables:

- A use case that deletes the expired Sessions, with a `SessionRepository` method that the use case calls.
- A task that calls the use case.
- Something that sends the task on a schedule.

## Edge cases

- The task uses the rule of `Session.is_active`: a Session is active only while `at < expires_at`, so a Session whose `expires_at` equals the time of the run is deleted.
- A run with no expired Session deletes nothing and succeeds.
- A worker that is down when the task is sent loses the task, because the ZeroMQ broker keeps no queue. The next run deletes the rows that the lost run missed.

## Out of scope

- A change of the taskiq broker.
- A change of the Session lifetime or of `session_end`.
- An index on `expires_at`, unless a measurement on the table shows the need.

## Acceptance criteria

- [ ] Given one expired Session and one active Session, when the task runs, then only the active Session remains.
- [ ] Given no expired Session, when the task runs, then every Session remains and the task succeeds.
- [ ] Given a Session whose `expires_at` equals the clock's time, when the task runs, then the Session is deleted.

## Open questions

- rastro has no taskiq scheduler today. Which process sends the task, and how often?
- With N workers, the ZeroMQ broker runs each task N times. A delete is idempotent, so is that acceptable here?
