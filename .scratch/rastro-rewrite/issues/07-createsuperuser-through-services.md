# 07: createsuperuser through services

**What to build:** Make `createsuperuser` create an administrator through the same services and rules as registration, so that an administrator follows the same email and password rules as everyone else. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

This ticket builds the first services, ports, adapters, and deps of `iam`:

- **The `PasswordHasher` port and its Django adapter.** The adapter has a line that checks it against the protocol.
- **The `deps` module.** It holds the real `PasswordHasher`.
- **The `identity_register` service.** It creates an Identity and raises `EmailInUseError` (`iam.email_in_use`) when the email is in use. It also catches the `IntegrityError` that a concurrent registration causes and raises the same error.
- **The `identity_register_superuser` service.** It does the same and also sets `is_staff` and `is_superuser`.
- **The minimal manager.** It holds only `create_user` and `create_superuser`. Each one parses its raw arguments into value objects, calls the matching service with the implementations from `deps`, and returns the Identity that it reads back.

The code that the old manager copied from Django's `UserManager` is deleted.

**Blocked by:** 04 (The RFC 9457 error contract), 06 (Tooling that checks the architecture)

**Status:** ready-for-agent

- [ ] `createsuperuser`, run through `call_command`, asks for the email, the display name, and the password, and creates an Identity with `is_staff` and `is_superuser` set.
- [ ] `createsuperuser` rejects an invalid email and a password shorter than 8 characters.
- [ ] Service tests, with a fake `PasswordHasher`, show that `identity_register` stores the hash that the hasher returns and raises `EmailInUseError` for an email in use.
- [ ] A service test shows that an `IntegrityError` on the unique email also raises `EmailInUseError`.
- [ ] Both services run in a transaction, take keyword-only value object arguments plus the `password_hasher`, and return `None`. The architecture tests pass on them.
- [ ] The manager has only `create_user` and `create_superuser`. `with_perm`, `normalize_email`, the `alters_data` markers, and `use_in_migrations` are gone.
- [ ] import-linter contracts cover the new ports, adapters, deps, and services modules.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
