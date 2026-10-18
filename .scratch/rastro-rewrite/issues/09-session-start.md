# 09: Session start

**What to build:** Replace the old login endpoint with `POST /api/v1/iam/session/start`, so that a person starts a Session with their Credentials and gets `204`. Nobody can tell from the answer or from its timing whether an email has an Identity. Read the spec (`.scratch/rastro-rewrite/PRD.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

This ticket builds:

- **The `Authenticator` port and its Django adapter.** The adapter uses Django's `authenticate`. It hashes a password even for an unknown email, upgrades an outdated hash, and refuses an inactive Identity.
- **The `SessionStore` port and its Django adapter.** The adapter starts, ends, and reads the Session through `login`, `logout`, and `get_user`. Every method receives the request.
- **The `session_start` service.** It raises `IncorrectCredentialsError` when the authenticator returns `None`.
- **The `session_start_api` view function and its input schema.**

The old Session start view, its use case, and the old password hashing service are deleted in this ticket.

**Blocked by:** 04 (The RFC 9457 error contract), 06 (Tooling that checks the architecture)

**Status:** ready-for-agent

- [ ] `POST /api/v1/iam/session/start` with correct Credentials answers `204` with no body and sets the session cookie.
- [ ] A wrong password and an unknown email both answer `401` with the type `/problems/iam.incorrect_credentials`.
- [ ] An inactive Identity answers the same `401`.
- [ ] A test shows that an unknown email runs the password hasher, so that its timing matches a wrong password.
- [ ] A Session start for an Identity with an outdated hash upgrades the stored hash.
- [ ] `last_login` of the Identity changes after a Session start.
- [ ] A service test with a fake authenticator that returns `None` raises `IncorrectCredentialsError` without using the database.
- [ ] Starting a Session again while one exists answers `204`.
- [ ] The old Session start endpoint, its use case, and the old password hashing service are deleted, and import-linter contracts cover the new modules.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
