# Reset the password of a User who forgot it

Status: needs-triage
Type: feature

## Problem

A User forgets the password. rastro has no route that changes a password without the old one, so the User cannot start a Session again, and only a manual change in the database restores the access.

## Solution

The User asks for a reset with the email address. rastro sends a link with a single-use reset token to that address. The User opens the link, presents the token and a new password, and rastro stores the new hash.

Deliverables:

- A route that receives an email address and sends the reset link.
- A route that receives the reset token and the new password and changes the password.
- A port that sends email, with an adapter for production and a fake for the tests.

## Edge cases

- An email address that matches no User gets the same response as one that matches, so the route does not tell who has a User.
- A used, expired, or unknown reset token changes nothing.
- A reset ends every Session of the User, so a stolen Session token stops working.

## Out of scope

- A password change for a User who knows the old password.
- Rate limits on the request route, unless `0004-audit-auth-against-owasp.md` asks for them.

## Acceptance criteria

- [ ] Given a User, when the client asks for a reset and then presents the token with a new password, then the Credentials with the new password start a Session, and the old password does not.
- [ ] Given a reset token that was used once, when the client presents it again, then the password stays the same.
- [ ] Given an email address with no User, when the client asks for a reset, then the response equals the response for a known address, and no email is sent.

## Open questions

- Does rastro store the reset token hashed, like the Session token, in a new table?
- How long does a reset token live?
- Which service sends the email, and does the send run in a taskiq task, which depends on `0005-evaluate-a-taskiq-broker-other-than-zeromq.md`?
