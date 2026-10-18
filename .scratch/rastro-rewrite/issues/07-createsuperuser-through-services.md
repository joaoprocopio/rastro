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

**Status:** done

- [x] `createsuperuser`, run through `call_command`, asks for the email, the display name, and the password, and creates an Identity with `is_staff` and `is_superuser` set.
- [x] `createsuperuser` rejects an invalid email and a password shorter than 8 characters.
- [x] Service tests, with a fake `PasswordHasher`, show that `identity_register` stores the hash that the hasher returns and raises `EmailInUseError` for an email in use.
- [x] A service test shows that an `IntegrityError` on the unique email also raises `EmailInUseError`.
- [x] Both services run in a transaction, take keyword-only value object arguments plus the `password_hasher`, and return `None`. The architecture tests pass on them.
- [x] The manager has only `create_user` and `create_superuser`. `with_perm`, `normalize_email`, the `alters_data` markers, and `use_in_migrations` are gone.
- [x] import-linter contracts cover the new ports, adapters, deps, and services modules.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket-07`, before the merge of `rastro-rewrite`:

- `src/rastro/iam/ports.py` holds `PasswordHasher`, a callable protocol from `RawPassword` to `HashedPassword`. `adapters.py` holds `django_make_password`, which calls Django's `make_password`, and the line `_: PasswordHasher = django_make_password` below it. `deps.py` holds `PASSWORD_HASHER: PasswordHasher = django_make_password` and nothing else.
- `services.py` holds `identity_register` and `identity_register_superuser`. Both have `@transaction.atomic`, take `email`, `display_name`, `password`, and `password_hasher` as keyword-only arguments, and return `None`. A private `_identity_create` checks the email, hashes the password, creates the Identity with the flags, and turns an `IntegrityError` into `EmailInUseError`. The architecture tests in `tests/architecture/` pass on both services.
- `src/rastro/iam/tests/services/` tests the services with a fake hasher: the stored hash is the one the hasher returns, an email in use raises `EmailInUseError`, and a hasher that inserts the same email before the service's insert makes the `IntegrityError` path raise `EmailInUseError` too. The superuser test checks `is_staff` and `is_superuser`, and the email-in-use test checks that the existing Identity keeps its flags.
- The manager holds only `create_user` and `create_superuser`, both keyword-only. Each one accepts a raw string or a value object for `email` and `display_name` (`createsuperuser` passes value objects because `field.clean()` ran, a direct call passes strings), parses them, turns an `InvalidValueError` into Django's `ValidationError` with the same code, calls the service with `deps.PASSWORD_HASHER`, and returns `self.get(email=...)`. A `password` of `None`, which `--noinput` passes without `DJANGO_SUPERUSER_PASSWORD`, counts as an empty password and fails `iam.invalid_password`. The manager imports `services` and `deps` inside the methods, because `services` imports `models` at module level. `with_perm`, `_create_user`, `_create_user_object`, the `alters_data` markers, and `use_in_migrations` are gone, and `test_models.py` checks that the public names of `IdentityManager` are exactly `create_user` and `create_superuser`. `normalize_email` stays available only as the inherited `BaseUserManager` classmethod. The initial migration no longer records the manager, and `makemigrations --check` reports no changes.
- `src/rastro/iam/tests/test_createsuperuser.py` runs `createsuperuser` through `call_command`. The interactive tests pass a `stdin` whose `isatty()` is true and replace `builtins.input` and `getpass.getpass`. The prompts are `Email: `, `Display name: `, `Password: `, and `Password (again): `, in that order, and the Identity has both flags and a usable password. An invalid email writes `Error: iam.invalid_email` to stderr and prompts again. A password of 5 characters raises `CommandError` with `iam.invalid_password`, in the interactive run and in the `--noinput` run with `DJANGO_SUPERUSER_PASSWORD`, and so does a `--noinput` run without the variable. A `--noinput` run with an email in use raises `EmailInUseError` from `create_superuser`, not a `CommandError`, because Django's uniqueness check only runs before the prompt. A `--noinput` run with an invalid email raises `InvalidValueError` from the lookup that Django's `_validate_username` runs through `get_by_natural_key` before `field.clean()`; neither case has a test.
- `pyproject.toml` gains `services` as the top layer of `iam layers` and three contracts: `services and selectors import no pydantic`, `services and selectors never import adapters`, and `only deps imports adapters` with `rastro.iam.deps -> rastro.iam.adapters` ignored. Two facts needed configuration that the spec does not name. The manager in `models` imports `services` and `deps`, so the layers contract ignores `rastro.iam.models -> rastro.iam.services` and the adapters contract ignores `rastro.iam.models -> rastro.iam.deps`. Every `values` module imports `rastro.common.values`, which imports Pydantic, so the pydantic contract sets `allow_indirect_imports = true` and checks direct imports only. A temporary `import pydantic` and `from rastro.iam import adapters` in `services.py`, plus the same adapters import in `admin.py`, broke the three new contracts and the report named the lines; I reverted the files.
- The old registration use case still writes through `Identity.objects.create` and its HTTP tests stay green, so it is unchanged; ticket 08 replaces it.
- The gate: `ruff check`, `ruff format --check`, `mypy`, `lint-imports` (5 kept, 0 broken), and `pytest` (126 passed) are green. `docker compose build django` builds the image. I did not run `docker compose up --build`, because the ports belong to the main directory; the merger runs the full stack.
