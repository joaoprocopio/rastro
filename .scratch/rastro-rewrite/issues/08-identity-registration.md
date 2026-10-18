# 08: Identity registration

**What to build:** Replace the old registration endpoint with `POST /api/v1/iam/identities/register`, so that a person registers an Identity, gets `201` with no body, and starts a Session as a separate step. Read the spec (`.scratch/rastro-rewrite/PRD.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The API is a view function named `identity_register_api`. It parses the body with the `IdentityRegisterInput` schema, which uses the value object types, and it calls `identity_register` with the implementations from `deps`. The old registration view, its use case, its DTOs, and the old URL are deleted in this ticket.

**Blocked by:** 07 (createsuperuser through services)

**Status:** ready-for-agent

- [ ] `POST /api/v1/iam/identities/register` with a valid body answers `201` with no body and no id.
- [ ] After registration, `GET` on the current Session does not show the new Identity, because registration starts no Session.
- [ ] An email in use answers `409` with the type `/problems/iam.email_in_use`.
- [ ] An invalid email, display name, or password answers `422`, with an `errors` item that points at the field and carries the value object's code.
- [ ] `" Ana@X.com "` registers the Identity `ana@x.com`.
- [ ] `GET` on the URL answers a problem details `405`.
- [ ] A request without a CSRF token answers `403` with the type `/problems/request.csrf_failed`.
- [ ] The old registration endpoint and its use case and DTOs are deleted, and import-linter contracts cover the new schemas and apis modules.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
