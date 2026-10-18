# 04: The RFC 9457 error contract

**What to build:** Replace the whole error pipeline, so that every error response from rastro, on the existing endpoints too, is an RFC 9457 problem details object with only `type` and `status`. A frontend or an API consumer can then map each problem type to its own message and never parses an HTML error page. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The spec's "Problem details" section holds the exact contract, including the JSON shape of a validation failure and the table that translates Pydantic errors to the `request.` codes.

This ticket builds:

- `ApplicationError` in `rastro.common`, with a code and no HTTP status;
- an errors module per app, starting with `iam`, with codes of the form `<app>.<name>`;
- a test that rejects a repeated code across apps;
- the problem details middleware, which holds the only table from code to HTTP status;
- the CSRF failure view and the `404` and `500` handlers;
- the API helpers `parse_body` and `respond`, plus `require_POST` and `require_GET`, which answer any other method with a problem details `405`.

The old `iam` code moves its errors to `ApplicationError` subclasses, so that the existing endpoints answer in the new format. The old middleware, `rastro/codes.py`, and the error and Problem classes of `rastro_base` are deleted in this ticket.

**Blocked by:** 03 (Building blocks in rastro.common)

**Status:** in-review

- [x] Every error response has the media type `application/problem+json` and carries only `type`, `status`, and, for a validation failure, `errors`. No response carries `title`, `detail`, or `code`.
- [x] A start of a Session with incorrect Credentials on the existing endpoint answers `401` with the type `/problems/iam.incorrect_credentials`.
- [x] A request body with a missing field, a wrong type, malformed JSON, or an unknown field answers `422` with the type `/problems/request.validation_failed` and one `errors` item per problem. Each item has a JSON Pointer and the matching `request.` type.
- [x] An `InvalidValueError` inside a request body appears as an `errors` item with the code of that error.
- [x] Every field error in a request appears in one response.
- [x] A CSRF failure answers `403` with the type `/problems/request.csrf_failed`.
- [x] An unknown URL answers `404` and an unhandled exception answers `500`, both as problem details without a `type`.
- [x] A test view decorated with `require_POST` answers a `GET` with a problem details `405` without a `type`, and the same holds for `require_GET`.
- [x] A test fails when two apps declare the same error code.
- [x] The old middleware, the central `ErrorCode` enum, and the `rastro_base` error and Problem classes are deleted.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [x] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Branch `ticket-04`, worktree `/home/jao/workspace/joaoprocopio/rastro-wt/ticket-04`. I verified each box through the gate or by hand:

- `rastro.common` gets `errors.py` (`ApplicationError`, `RequestCode`), `apis.py` (`parse_body`, `respond`, `require_POST`, `require_GET`, `problem_response`), `middleware.py` (`ProblemDetailsMiddleware` and `STATUS_BY_CODE`, the only table from code to status), and `views.py` (`csrf_failure`, `not_found`, `server_error`). `rastro.iam.errors` declares `iam.email_in_use`, `iam.incorrect_credentials`, and `iam.not_authenticated`.
- `src/rastro/common/tests/test_apis.py` posts to a sample API under `rastro.common.tests.sample` and reads one `errors` item per problem: `#/coats` with `request.field_required`, `request.invalid_type` for `"two"`, `#` with `request.invalid_json` for `{not valid`, `#/brush` with `request.unknown_field`, and `#/color` with `sample.invalid_color` from the `InvalidValueError`. One request with three problems answers three items. A problem carries only `type`, `status`, and `errors`.
- `require_POST` and `require_GET` answer the other method with `405`, `{"status": 405}`, and an `Allow` header.
- `src/rastro/common/tests/test_views.py` shows `403` with `request.csrf_failed` through `Client(enforce_csrf_checks=True)`, `404` as `{"status": 404}` on `/nope`, and `500` as `{"status": 500}` through `Client(raise_request_exception=False)` on a sample view that raises.
- The old endpoints answer `401` with `iam.incorrect_credentials` on wrong Credentials, and `GET /session` without a Session now answers `401` with `iam.not_authenticated` instead of a bare `401`.
- `tests/architecture/test_error_codes.py` finds each app's `errors.py` from `INSTALLED_APPS`, fails on a repeated code (verified with a temporary duplicate in `iam`, then reverted), and checks that every `ApplicationError` code has a row in `STATUS_BY_CODE`.
- `rastro/middleware.py`, `rastro/codes.py`, `rastro_base/error.py`, `rastro_base/problem.py`, `rastro/iam/domain/errors.py`, and their tests are deleted.
- The gate is green: `ruff check`, `ruff format --check`, `mypy` (68 files), and `pytest` (62 tests) with `RASTRO_POSTGRES_DB=ticket_04`.
- The brief forbids `docker compose up` in a worktree, so I ran `docker compose build django` and served the image with `docker run --network host` against the `ticket_04` database on port 8004: `migrate` applied every migration, `GET /nope` answered `{"status": 404}`, `GET /api/v1/iam/session` answered `iam.not_authenticated`, a `POST` without a CSRF token answered `request.csrf_failed`, and `GET /admin/login/` answered `200`. The merger runs the full stack on the integration branch.
