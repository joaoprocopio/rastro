# 10: Current Session, end of Session, and the CSRF cookie

**What to build:** Replace the remaining old endpoints, so that a frontend can read the current Session, end it, and get its CSRF cookie through the new contract. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The operations are:

- `GET /api/v1/iam/session`, through the selector `identity_get_current`, which takes the `request` and the `session_store`. It answers `200` with `email` and `display_name`, or the problem `iam.not_authenticated`.
- `POST /api/v1/iam/session/end`, through the service `session_end`, which succeeds whether or not a Session exists.
- `GET /api/v1/iam/csrf`, which sets the `csrftoken` cookie and answers `204`.

The old `GET` and `DELETE` handlers on the Session URL, the old CSRF token URL, and their use cases are deleted in this ticket.

**Blocked by:** 09 (Session start)

**Status:** done

- [x] `GET /api/v1/iam/session` with a Session answers `200` with exactly `email` and `display_name`, and with no id.
- [x] `GET /api/v1/iam/session` without a Session answers `401` with the type `/problems/iam.not_authenticated`.
- [x] `POST /api/v1/iam/session/end` answers `204` and ends the Session, so that a following `GET /api/v1/iam/session` answers `401`.
- [x] `POST /api/v1/iam/session/end` without a Session also answers `204`.
- [x] `GET /api/v1/iam/csrf` answers `204` and sets a `csrftoken` cookie that JavaScript can read.
- [x] The output schema is `SessionCurrentOutput` and no other operation reuses it.
- [x] The old Session `GET` and `DELETE` handlers, the old CSRF token URL, and their use cases are deleted, and import-linter contracts cover the new selectors module.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`, plus `lint-imports`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket-10`, before the merge of `rastro-rewrite`:

- `src/rastro/iam/selectors.py` holds `identity_get_current`, which takes `request` and `session_store`, returns the Identity of the current Session, and raises `NotAuthenticatedError` when `session_store.current` returns `None`. `services.py` gains `session_end`, which takes `request` and `session_store` and calls `session_store.end`. Both services now carry `@transaction.atomic`, as `CODING_STANDARDS.md` says, so every service test uses the test database.
- `schemas.py` holds `SessionCurrentOutput` with `email` and `display_name`, and only `session_current_api` builds it. `StrValueObject` already returns a `json_or_python_schema` whose Python side accepts a built instance, so the API fills the schema from the model attributes with no change to `rastro.common.values`.
- `apis.py` holds `session_current_api` (`require_GET`), `session_end_api` (`require_POST`), and `csrf_get_api` (`require_GET` over `ensure_csrf_cookie`, which answers `204` with the `csrftoken` cookie). `urls.py` routes `session`, `session/start`, `session/end`, and `csrf`. The CSRF view has no entity of its own in `GLOSSARY.md`, so its name reads `csrf_get_api`; this is a question for the user if another name fits the `<entity>_<action>_api` rule better.
- The HTTP tests live in `src/rastro/iam/tests/apis/test_session_current.py`, `test_session_end.py`, and `test_csrf.py`. The CSRF test reads the cookie from `response.cookies["csrftoken"]` and asserts that `httponly` is off. The service and selector tests in `tests/services/test_session_end.py` and `tests/selectors/test_identity_get_current.py` pass a fake `SessionStore`.
- `SessionView`, `CsrfTokenView`, `GetCurrentIdentityUseCase`, `EndSessionUseCase`, `django_get_current_identity_use_case_factory`, `django_end_session_use_case_factory`, and the `end` and `current_identity` methods of `SessionService` and `DjangoSessionService` are deleted. `presentation/urls.py` keeps only `identities`, and `IdentitiesView`, `RegisterIdentityUseCase`, the DTOs, and the mappers stay for ticket 08. The old register tests end the Session through `POST /session/end`.
- `pyproject.toml` adds `services : selectors` as one layer in `iam layers` and `rastro.iam.selectors` to the source modules of `services and selectors import no pydantic` and `services and selectors never import adapters`. A temporary `import pydantic` and `from rastro.iam import adapters, apis, schemas` in `selectors.py` broke five contracts; the file is restored.
- The gate: `ruff check`, `ruff format --check`, `mypy`, `lint-imports` (6 kept, 0 broken), and `pytest` (120 passed) are green. `docker compose build django` builds the image. I did not run `docker compose up --build`, because the ports belong to the main directory; the merger runs the full stack.
