# 03: Handle the SMTP failures

Status: ready-for-agent
Blocked by: 01

Spec: `.scratch/password-reset/spec.md`

**What to build:** A send that fails follows the table of send outcomes in the spec. A brief SMTP failure retries, so the User still receives the email. A refusal ends the job as `failed` at once. A disconnection or a timeout after the connection opens keeps the token and sends nothing more, so an email that did go out holds a link that works, and the User receives no duplicate. Read the source of the chosen SMTP library before you map its exceptions to the errors of the port.

- [ ] Given a connection failure or an SMTP 4xx, when the job runs, then no token commits, and the job retries with `exponential_wait=2` and `max_attempts=10`.
- [ ] Given an SMTP 5xx, when the job runs, then no token commits, and the job ends as `failed` with no retry.
- [ ] Given a disconnection or a timeout after the connection opens, when the job runs, then the token commits, the job succeeds with no retry, and a warning log exists.
- [ ] Given a temporary failure on every attempt, when the attempts run out, then the job ends as `failed`.
- [ ] Given a temporary failure and then an accepted send, when the job finishes, then one Reset token exists, and the token of the email works.
- [ ] Given a test SMTP server, when it answers each kind of response, then the SMTP adapter raises the matching error of the port.
