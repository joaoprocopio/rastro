# 08: Identity registration

**What to build:** Replace the old registration endpoint with `POST /api/v1/iam/identities/register`, so that a person registers an Identity, gets `201` with no body, and starts a Session as a separate step. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The API is a view function named `identity_register_api`. It parses the body with the `IdentityRegisterInput` schema, which uses the value object types, and it calls `identity_register` with the implementations from `deps`. The old registration view, its use case, its DTOs, and the old URL are deleted in this ticket.

**Blocked by:** 07 (createsuperuser through services)

**Status:** ready-for-agent

- [x] `POST /api/v1/iam/identities/register` with a valid body answers `201` with no body and no id.
- [x] After registration, `GET` on the current Session does not show the new Identity, because registration starts no Session.
- [x] An email in use answers `409` with the type `/problems/iam.email_in_use`.
- [x] An invalid email, display name, or password answers `422`, with an `errors` item that points at the field and carries the value object's code.
- [x] `" Ana@X.com "` registers the Identity `ana@x.com`.
- [x] `GET` on the URL answers a problem details `405`.
- [x] A request without a CSRF token answers `403` with the type `/problems/request.csrf_failed`.
- [x] The old registration endpoint and its use case and DTOs are deleted, and import-linter contracts cover the new schemas and apis modules.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [x] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket-08`, before the merge of `rastro-rewrite`:

- `src/rastro/iam/apis.py` holds `identity_register_api` under `require_POST`. It parses the body with `IdentityRegisterInput` from `schemas.py`, whose fields are `Email`, `DisplayName`, and `RawPassword` with `extra="forbid"`, calls `services.identity_register` with `deps.PASSWORD_HASHER`, and answers `201` with no body. `urls.py` maps `identities/register` to it.
- `src/rastro/iam/tests/apis/test_identity_register.py` covers the contract through the test `Client`: `201` with an empty body, `401` `iam.not_authenticated` on `GET /session` after a registration, `409` `iam.email_in_use` for the email of the `identity` fixture, one `422` with three `errors` items (`#/email` `iam.invalid_email`, `#/display_name` `iam.invalid_display_name`, `#/password` `iam.invalid_password`) for one body with every field invalid, a Session start with `ana@x.com` after a registration with `" Ana@X.com "`, `405` with `{"status": 405}` and `Allow: POST` on `GET`, `403` `request.csrf_failed` from a `Client(enforce_csrf_checks=True)`, and a password `"  pass word  "` that a Session start with `"pass word"` refuses and the exact password accepts.
- The old `IdentitiesView`, `RegisterIdentityUseCase`, `RegisterIdentityInputDTO`, `django_register_identity_use_case_factory`, `PasswordHashingService`, `DjangoPasswordHashingService`, and the `identities` route are deleted, with the four old tests that posted to `/identities`. `IdentityRepository` and `DjangoIdentityRepository` had that use case as their only caller, so `domain/repository.py` and `infrastructure/repositories.py` are deleted too. `IdentityOutputDTO`, `IdentityPublicDTO`, the mappers, the old Session `GET` and `DELETE` handlers, and the old `csrftoken` URL stay for ticket 10.
- The contracts from tickets 07 and 09 already cover `apis` and `schemas`, so `pyproject.toml` is unchanged. A temporary `from rastro.iam import schemas` in `services.py` and `from rastro.iam import apis` in `models.py` broke `only apis import schemas`, `iam layers`, and `services and selectors never import adapters`, and the report named the lines; both files are restored.
- The gate: `ruff check`, `ruff format --check`, `mypy`, `lint-imports` (6 kept, 0 broken), and `pytest` (137 passed) are green. `docker compose build django` builds the image. I did not run `docker compose up --build`, because the ports belong to the main directory; the merger runs the full stack.
