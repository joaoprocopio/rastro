# 02: Run one behaviour suite against each fake and Sql repository

**What to build:** A use case test that passes with a fake repository also passes on Postgres, because each fake passes the same behaviour suite as its Sql adapter. The suite covers `UserRepository`, `SessionRepository`, and the sample app's `NoteRepository`. A parametrized fixture returns the fake or the Sql adapter, and only the Sql case opens the database. The Sql case reads back through a second database session. Each behaviour has one test, so the behaviour tests leave the per-adapter test modules. Read the spec (`.scratch/architecture-deepening/spec.md`, section "2. One behaviour suite per repository port"), `CODING_STANDARDS.md`, and the ADRs before you start.

The fakes change to pass the suite: `FakeUserRepository.add` raises `EmailInUseError` for an email in use, every fake `remove` raises `LookupError` with a message for a missing id, and `FakeNoteRepository` stores and returns a `model_copy()`. These tests stay Sql-only: a row that breaks its value object (the bad email and the id `0`), the audit columns that the database sets, and the query span that keeps no parameters.

**Blocked by:** 01 (Delete the repository methods that no use case calls), so the suite holds no test for a deleted method.

**Status:** ready-for-agent

- [ ] Given a User with the email `ana@x.com` in the repository, when a second User with `ana@x.com` is added, then both the fake and the Sql adapter raise `EmailInUseError`.
- [ ] Given no aggregate with a given id, when `update` or `remove` runs for that id, then both adapters raise `LookupError` and the repository stays unchanged.
- [ ] Given an aggregate read from the repository, when a test assigns a field and calls no `update`, then a second read from either adapter returns the old value. This holds for `FakeNoteRepository` too.
- [ ] Each behaviour test runs once per adapter, and no behaviour has a second test in a per-adapter module.
- [ ] The checks in `README.md` pass.
