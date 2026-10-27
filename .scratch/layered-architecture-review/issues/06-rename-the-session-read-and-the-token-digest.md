# 06: Rename the Session read and the token digest

**What to build:** The operation behind `GET /api/v1/auth/session` takes the name `session_get`, each application mapper takes the name of its Output DTO, and the digest of a Session token takes the name `HashedSessionToken` with the field and column `hashed_token`. The JSON of every route stays the same. Read the spec (`.scratch/layered-architecture-review/spec.md`, section Names), `CODING_STANDARDS.md`, the ADRs, and the Decisions of tickets 01 to 05 before you start, and follow the auto mode that the spec's Further Notes describe.

Rename the use case, its Output DTO, its view, and its mapper as the spec lists. Rename `SessionTokenHash`, the `Session` field, the `auth_session` column, and the repository lookup. Nothing is deployed, so edit the initial revision of `auth_session` in place. State the mapper name rule in `CODING_STANDARDS.md`, and update every other name that the documentation cites.

**Blocked by:** 03, 04, 05

**Status:** ready-for-agent

- [ ] Every HTTP test passes with an unchanged assertion, and the JSON of `GET /api/v1/auth/session` does not change.
- [ ] The migration test passes, and the `auth_session` table has a `hashed_token` column and no `token_hash` column.
- [ ] A search of the source and the documentation for `user_get_current`, `UserGetCurrentOutput`, `SessionTokenHash`, and `token_hash` finds nothing.
- [ ] `CODING_STANDARDS.md` states that an application mapper takes the name of its Output DTO, for example `session_get_output`.
- [ ] Every check in the README passes.

## Comments
