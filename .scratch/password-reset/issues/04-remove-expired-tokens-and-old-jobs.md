# 04: Remove expired Reset tokens and old reset jobs

Status: ready-for-agent
Blocked by: 01

Spec: `.scratch/password-reset/spec.md`

**What to build:** rastro removes what it no longer needs without an operator. An hourly task removes the expired Reset tokens, and a daily task removes the finished reset jobs older than 7 days with their email addresses, the failed jobs included.

- [ ] Given an expired Reset token and a valid one, when the hourly task runs, then only the expired row is gone, and the task logs the count.
- [ ] Given a finished reset job older than 7 days and a failed one of the same age, when the daily task runs, then both rows are gone.
- [ ] Given a finished reset job younger than 7 days, when the daily task runs, then the row stays.
- [ ] Given a finished job of another queue older than 7 days, when the daily task runs, then the row stays.
