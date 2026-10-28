# Renew the Session while the client uses it

Status: needs-triage
Type: feature

## Problem

A User signs in and uses rastro every day. The Session still ends when `session_lifetime` runs out, 14 days after `session_start` by default, because `Session.start` sets `expires_at` once and no code moves it. The User then has to present the Credentials again in the middle of their work.

## Solution

A request that presents an active Session moves its `expires_at` forward by `session_lifetime`, and the response rewrites the Session cookie with the new expiry. A client that stops using rastro still loses the Session one `session_lifetime` after its last request.

Deliverables:

- An aggregate method on `Session` that renews it at a given time, so the rule lives with `is_active`.
- A use case step that renews the Session and writes it with `sessions.update`.
- A view change that passes the new expiry to `session_cookie_set`.

## Edge cases

- An expired Session is not renewed, and the request still answers `401 auth.not_authenticated`.
- `session_end` does not renew the Session that it removes.
- Two parallel requests renew the same Session, and the later write wins. Both expiries are valid, so the order does not matter.

## Out of scope

- The deletion of expired Sessions, which `0001-delete-expired-sessions.md` covers.
- A "remember me" choice at `session_start`.

## Acceptance criteria

- [ ] Given an active Session, when the client sends a request at time T, then the Session's `expires_at` is T plus `session_lifetime`, and the cookie's `Expires` matches it.
- [ ] Given an expired Session, when the client sends a request, then the response is `401 auth.not_authenticated`, and the row keeps its `expires_at`.

## Open questions

- A renewal writes the row on every authenticated request. Does rastro renew on every request, or only when less than half of `session_lifetime` remains, so most requests write nothing?
- Does a Session get an absolute limit, for example 90 days after `session_start`, after which the User presents the Credentials again even while active?
- Which requests renew the Session: only `GET /api/v1/auth/session`, or every route that reads the Session token? The answer depends on the `CurrentUser` dependency, which a later spec decides.
