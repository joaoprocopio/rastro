# 02: Shared test fixtures per app

**What to build:** Rebuild the test setup around reusable fixtures, so that a test asks for the state it needs by name and no test file carries a private copy of a setup helper. The tests cover the same behaviour as before. Read the spec (`.scratch/rastro-review-fixes/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start, and follow the auto mode that the spec's Further Notes describe.

The `iam` test package gets a `conftest.py` with `identity`, `signed_in_client`, `admin_client`, `session_store`, and `password_hasher`. A fixture that more than one app uses lives in the root `conftest.py`, and the `identity` fixture moves out of it. A variation of the shared state calls the factory in the test. `force_login` starts a Session everywhere except in the tests of `session_start`. Tests post JSON through the Django test client with `content_type="application/json"`, and they build URLs with `reverse()`. Test classes are optional.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] The `iam` test package's `conftest.py` holds the five fixtures above, and the root `conftest.py` holds no `iam` fixture.
- [ ] No test file defines `_start_session`, `_post`, `_register`, or `_post_json`, and no test file defines a URL constant.
- [ ] Every test that needs a Session, other than the `session_start` tests, starts it with `force_login`.
- [ ] HTTP tests still compare the literal JSON of each problem, and service tests still assert the error class.
- [ ] The test section of `CODING_STANDARDS.md` tells an agent to look in the app's `conftest.py` for a fixture that builds the state a test needs before it writes the test, and to add a fixture when two tests need the same state.
- [ ] Every decision that the spec did not settle is recorded under `## Comments`, as the spec's Further Notes describe.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
