# 09: Session start

**What to build:** Replace the old login endpoint with `POST /api/v1/iam/session/start`, so that a person starts a Session with their Credentials and gets `204`. Nobody can tell from the answer or from its timing whether an email has an Identity. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

This ticket builds:

- **The `Authenticator` port and its Django adapter.** The adapter uses Django's `authenticate`. It hashes a password even for an unknown email, upgrades an outdated hash, and refuses an inactive Identity.
- **The `SessionStore` port and its Django adapter.** The adapter starts, ends, and reads the Session through `login`, `logout`, and `get_user`. Every method receives the request.
- **The `session_start` service.** It raises `IncorrectCredentialsError` when the authenticator returns `None`.
- **The `session_start_api` view function and its input schema.**

The old Session start view, its use case, and the old password hashing service are deleted in this ticket.

**Blocked by:** 04 (The RFC 9457 error contract), 06 (Tooling that checks the architecture)

**Status:** resolved

- [x] `POST /api/v1/iam/session/start` with correct Credentials answers `204` with no body and sets the session cookie.
- [x] A wrong password and an unknown email both answer `401` with the type `/problems/iam.incorrect_credentials`.
- [x] An inactive Identity answers the same `401`.
- [x] A test shows that an unknown email runs the password hasher, so that its timing matches a wrong password.
- [x] A Session start for an Identity with an outdated hash upgrades the stored hash.
- [x] `last_login` of the Identity changes after a Session start.
- [x] A service test with a fake authenticator that returns `None` raises `IncorrectCredentialsError`. The test uses a fake authenticator against the test database.
- [x] Starting a Session again while one exists answers `204`.
- [x] The old Session start endpoint, its use case, and the old password hashing service are deleted, and import-linter contracts cover the new modules.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [x] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket-09`, before the merge of `rastro-rewrite`:

- `src/rastro/iam/ports.py` declares `Authenticator` (a callable that takes `request`, `email`, and `password` and returns `Identity | None`) and `SessionStore` (`start`, `end`, and `current`, each with the `request`). `adapters.py` holds `django_authenticate` over `django.contrib.auth.authenticate` and `DjangoSessionStore` over `login`, `logout`, and `get_user`. `deps.py` holds `AUTHENTICATE` and `SESSION_STORE`.
- The two protocol check lines in `adapters.py` are `_authenticator: Authenticator = django_authenticate` and `_session_store: SessionStore = DjangoSessionStore()`. mypy rejects a second annotated assignment to `_` in one module (`no-redef`), so each adapter uses a name of its own. `CODING_STANDARDS.md` shows `_`, and this is a question for the user.
- `session_start` checks the Credentials first and opens `transaction.atomic()` as a `with` block around `session_store.start`, so the service test with a fake authenticator that refuses runs without the `db` fixture. The `@transaction.atomic` decorator form opens the transaction before the authenticator runs, and pytest-django then rejects the test with "Database access not allowed". `CODING_STANDARDS.md` says "A service that writes has `@transaction.atomic`", so this is a question for the user. The test that starts a Session through the fakes uses `db`, because the transaction needs a connection.
- The HTTP tests live in `src/rastro/iam/tests/apis/test_session_start.py`. The unknown-email test places `RecordingHasher`, a test-only `MD5PasswordHasher` subclass that records every `encode` call, first in `PASSWORD_HASHERS` through `override_settings`, and asserts that the hasher encoded the submitted password once. The upgrade test installs `PBKDF2PasswordHasher` beside MD5, stores a pbkdf2 hash, starts a Session, and reads back an `md5$` hash that still checks the password.
- The old `SessionView.post`, `AuthenticateUseCase`, `AuthenticateInputDTO`, `django_authenticate_use_case_factory`, `IdentityAggregate.verify_password` and `update_password`, `IdentityRepository.update_password`, and the `verify` side of `PasswordHashingService` are deleted. `PasswordHashingService.hash` and `DjangoPasswordHashingService` stay, because the old `RegisterIdentityUseCase` still calls `hash`. Ticket 08 deletes them with that use case.
- `src/rastro/iam/urls.py` holds the new route, and `rastro/urls.py` includes it beside the old `presentation/urls.py` for `GET /session`, `DELETE /session`, `POST /identities`, and `GET /csrftoken`, which tickets 08 and 10 replace. The old tests that started a Session now post to `/session/start`.
- `pyproject.toml` adds `apis` and `services` to the `iam layers` contract and four forbidden contracts: `only apis import schemas`, `services and selectors import no pydantic`, `services and selectors never import adapters`, and `only deps imports adapters`. The first, second, and fourth set `allow_indirect_imports`, because `urls -> apis -> schemas`, `services -> ports -> models -> rastro.common.values -> pydantic`, and `apis -> deps -> adapters` are allowed chains. A temporary `import pydantic`, `from rastro.iam import adapters`, and `from rastro.iam import schemas` in `services.py`, plus `from rastro.iam import apis` in `values.py`, broke all six contracts; the files are restored. `selectors` joins the contracts in ticket 10, because import-linter fails on a module that does not exist.
- The gate: `ruff check`, `ruff format --check`, `mypy`, `lint-imports` (6 kept, 0 broken), and `pytest` (115 passed) are green. `docker compose build django` builds the image. I did not run `docker compose up --build`, because the ports belong to the main directory; the merger runs the full stack.
- Update after review: the user chose the `@transaction.atomic` decorator on `session_start` and `session_end`, so the service test with the fake authenticator now runs on the test database through the `db` fixture.

## Answer

Merged into `rastro-rewrite` in `1ca15d3`. The merge ran the full check gate and a smoke run of the built image against a fresh database.
