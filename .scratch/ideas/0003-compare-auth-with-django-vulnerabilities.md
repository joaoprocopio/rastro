# Compare auth with the vulnerabilities found in Django's auth

Status: needs-triage
Type: spike

## Problem

Django's authentication has years of public security advisories, and each one names a mistake that a hand-written auth can repeat. rastro wrote its own auth on FastAPI, so no one has checked whether `src/rastro/auth` repeats any of those mistakes.

## Solution

The spike lists every security advisory that touched `django.contrib.auth`, its password hashers, and its sessions, and checks each one against rastro. The result is a Markdown table with one row per advisory: the CVE, the mistake in one sentence, and whether rastro has the same mistake, with the file and line as evidence.

Deliverables:

- The table, in `.scratch/` beside this idea.
- One ticket for each advisory that rastro repeats.

## Out of scope

- The fix of a vulnerability that the spike finds. Each fix gets its own ticket.
- Advisories outside auth and sessions, for example in the ORM or the template engine.

## Acceptance criteria

- [ ] Every advisory in Django's security archive that touches auth, password hashing, or sessions has one row in the table.
- [ ] Each row that says "not affected" cites the rastro code that prevents the mistake.

## Open questions

- Is Django's security archive the only source, or do the CVE database and the Django release notes add advisories that the archive misses?
