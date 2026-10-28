# Audit auth against OWASP

Status: needs-triage
Type: spike

## Problem

rastro's auth registers a User, starts a Session from the Credentials, reads the Session, and ends it. No one has checked these four routes against a public security standard, so a known class of attack may still work against them.

## Solution

The spike audits `src/rastro/auth` and the `csrf` app against the OWASP material that applies to authentication and sessions. The result is a checklist with one line per requirement: met, not met, or not applicable, with the file and line as evidence.

Candidate sources, to narrow in the spike:

- OWASP ASVS, the chapters on authentication, session management, and passwords.
- OWASP Cheat Sheets: Authentication, Session Management, Password Storage, Credential Stuffing Prevention, and Forgot Password.
- OWASP Top 10, A07 Identification and Authentication Failures.

Deliverables:

- The checklist, in `.scratch/` beside this idea.
- One ticket for each requirement that rastro does not meet and that is worth the cost.

## Out of scope

- The fixes. Each fix gets its own ticket.
- OWASP chapters outside auth and sessions.

## Acceptance criteria

- [ ] Every requirement of the chosen sources has one line in the checklist.
- [ ] Each "met" line cites the rastro code or test that meets it.

## Open questions

- Which ASVS level does rastro target: 1, 2, or 3?
- Does the spike merge with `0003-compare-auth-with-django-vulnerabilities.md`, because both read the same code and produce tickets of the same kind?
