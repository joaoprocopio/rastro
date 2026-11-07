# 01: Reset the password on the happy path

Status: ready-for-agent
Blocked by: None (can start immediately)

Spec: `.scratch/password-reset/spec.md`

**What to build:** A User asks for a reset with the email address, receives an email with a link in Mailpit, and presents the Reset token of the link with a new password. rastro stores the new hash and ends every Session of the User. An address with no User gets the same response and no email. This ticket adds the defer helper of ADR 0004, the Reset token table, the settings of the spec, Mailpit in the local stack, and the email port, which `create_worker_app` receives and the task reads from the job context.

This ticket handles only an accepted send. The cooldown, the replacement rule beyond the unique row, the send failures, and the cleanup belong to the later tickets.

- [ ] Given a User, when the client asks for a reset, the worker runs, and the client presents the token of the email with a new password, then the Credentials with the new password start a Session, and the old password does not.
- [ ] Given a User with active Sessions, when a confirmation succeeds, then every Session of the User has ended, and the response starts no Session.
- [ ] Given an email address with no User, when the client asks for a reset and the worker runs, then the response equals the response for a known address, a job exists, and no email goes out.
- [ ] Given a malformed email address, when the client asks for a reset, then the response is `422`.
- [ ] Given a Reset token that was used once, when the client presents it again, then the response is `400 auth.invalid_reset_token`, and the password stays the same.
- [ ] Given an expired or unknown Reset token, when the client presents it, then the response is the same `400 auth.invalid_reset_token`.
- [ ] Given two concurrent confirmations with one Reset token, when both run, then one answers `204`, and the other answers `400 auth.invalid_reset_token`.
- [ ] Given a new password that `RawPassword` rejects, when the client presents it with a valid token, then the response is `422`, and the token still works.
- [ ] Given an email that went out, when a test reads the Reset token table and the job arguments, then neither holds the token of the link.
- [ ] Given the local stack, when a User asks for a reset, then Mailpit shows a plain text email in en-US with the link and its lifetime, and the token sits in the fragment of the link.
