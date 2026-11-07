# 02: Keep one valid link and a cooldown between emails

Status: ready-for-agent
Blocked by: 01

Spec: `.scratch/password-reset/spec.md`

**What to build:** A User who asks twice has one valid link, the link of the last email. A second request within the cooldown of 60s sends nothing and keeps the current link, so a person who knows the address cannot flood the inbox at that rate. The response of the request route does not change in either case.

- [ ] Given two requests of one User more than 60s apart, when the client presents the first token, then the response is `400 auth.invalid_reset_token`, and the second token works.
- [ ] Given two requests of one User within 60s, when the worker runs both jobs, then one email goes out, and the token of that email works.
- [ ] Given two jobs of one User that run at the same time, when both finish, then one Reset token exists for the User, and it is the token of the last email that went out.
- [ ] Given a cooldown setting with another value, when the worker runs a second request, then the use case applies that value.
