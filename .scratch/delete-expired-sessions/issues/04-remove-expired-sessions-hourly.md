# 04: Remove each expired Session every hour

**What to build:** every hour, rastro removes each Session whose lifetime has run out, and the log shows how many it removed. The `SessionRepository` port gains `remove_expired(*, at)`, which returns the number of removed Sessions. The Sql adapter runs one `DELETE` of every row whose `expires_at <= at`, and the fake applies the same rule. The rule mirrors `Session.is_active`, so a Session whose `expires_at` equals `at` is expired. The use case `session_remove_expired` takes the `sessions` repository and the `clock` as keyword-only ports, reads the time once from `Clock.now()`, and returns a `SessionRemoveExpiredOutput` with the count. The task `session_remove_expired_task` runs on the cron `0 * * * *`, calls the use case, and writes the count to the log with the standard library logger. The task has no retry strategy, because the next tick does the same work. The spec is `.scratch/delete-expired-sessions/spec.md`.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Given one expired Session and one active Session, when `remove_expired` runs, then only the active Session remains, for the fake and the Sql adapter.
- [ ] Given a Session whose `expires_at` equals `at`, when `remove_expired` runs, then the Session is removed, for the fake and the Sql adapter.
- [ ] Given no expired Session, when `remove_expired` runs, then every Session remains and it returns 0, for the fake and the Sql adapter.
- [ ] The use case removes the Sessions that expired at the time of `FakeClock`, and its output holds the count.
- [ ] Given one expired Session and one active Session, when `session_remove_expired_task` runs through the `InMemoryConnector`, then only the active Session remains.
- [ ] The worker registers `session_remove_expired_task` on the cron `0 * * * *`.
- [ ] Every check in the README passes.
