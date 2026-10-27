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

### Decisions

- **Gap: the name of the unique constraint on the digest.** The initial revision and `SessionRow` named it `auth_session_token_hash_key`. Chosen: `auth_session_hashed_token_key`, the name that Postgres gives by default to a unique constraint on `hashed_token`, edited in place in both files. Rejected: keeping the old name, which names a column that no longer exists and fails the search for `token_hash`.
- **Gap: how the migration test shows the `hashed_token` column and the absence of the old one.** Chosen: `test_the_session_table_stores_the_hashed_token` in `src/rastro/tests/test_migrations.py` compares the ordered list of every column of `auth_session` with a literal list, so the old column fails the test with no literal of its name. Rejected: an assertion that names the old column, which puts `token_hash` back in the source; relying on `test_the_migrations_create_every_table_of_the_models` alone, which passes with any name while the row and the revision agree.
- **Gap: the names in the tests that cite the old names.** Chosen: the test files become `test_session_get.py` in `tests/views/` and `tests/use_cases/`, the two repository tests name `get_by_hashed_token`, and the local `current` in the use case test becomes `output`. Rejected: keeping a name that cites an operation that no longer exists.
- **Gap: whether the mapper name rule covers the infrastructure mappers.** Chosen: the rule in "Map between layers by hand" names only the application mappers, as the spec does, and `session_from_row` and `note_from_row` keep their names. Rejected: renaming the infrastructure mappers, which is outside the spec.
- **Gap: the review comments of the spec's Cleanup.** A search of every comment and docstring in the code found no review comment left by tickets 01 to 05. The one `TODO` in `compose.yaml` comes from the first commit, before the review, and addresses no author. Chosen: keep it. Rejected: removing it, which the spec does not ask.
