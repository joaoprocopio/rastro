# 10: Current Session, end of Session, and the CSRF cookie

**What to build:** Replace the remaining old endpoints, so that a frontend can read the current Session, end it, and get its CSRF cookie through the new contract. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The operations are:

- `GET /api/v1/iam/session`, through the selector `identity_get_current`, which takes the `request` and the `session_store`. It answers `200` with `email` and `display_name`, or the problem `iam.not_authenticated`.
- `POST /api/v1/iam/session/end`, through the service `session_end`, which succeeds whether or not a Session exists.
- `GET /api/v1/iam/csrf`, which sets the `csrftoken` cookie and answers `204`.

The old `GET` and `DELETE` handlers on the Session URL, the old CSRF token URL, and their use cases are deleted in this ticket.

**Blocked by:** 09 (Session start)

**Status:** ready-for-agent

- [ ] `GET /api/v1/iam/session` with a Session answers `200` with exactly `email` and `display_name`, and with no id.
- [ ] `GET /api/v1/iam/session` without a Session answers `401` with the type `/problems/iam.not_authenticated`.
- [ ] `POST /api/v1/iam/session/end` answers `204` and ends the Session, so that a following `GET /api/v1/iam/session` answers `401`.
- [ ] `POST /api/v1/iam/session/end` without a Session also answers `204`.
- [ ] `GET /api/v1/iam/csrf` answers `204` and sets a `csrftoken` cookie that JavaScript can read.
- [ ] The output schema is `SessionCurrentOutput` and no other operation reuses it.
- [ ] The old Session `GET` and `DELETE` handlers, the old CSRF token URL, and their use cases are deleted, and import-linter contracts cover the new selectors module.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
