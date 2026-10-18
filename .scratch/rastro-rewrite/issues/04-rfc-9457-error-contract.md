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

**Status:** ready-for-agent

- [ ] Every error response has the media type `application/problem+json` and carries only `type`, `status`, and, for a validation failure, `errors`. No response carries `title`, `detail`, or `code`.
- [ ] A start of a Session with incorrect Credentials on the existing endpoint answers `401` with the type `/problems/iam.incorrect_credentials`.
- [ ] A request body with a missing field, a wrong type, malformed JSON, or an unknown field answers `422` with the type `/problems/request.validation_failed` and one `errors` item per problem. Each item has a JSON Pointer and the matching `request.` type.
- [ ] An `InvalidValueError` inside a request body appears as an `errors` item with the code of that error.
- [ ] Every field error in a request appears in one response.
- [ ] A CSRF failure answers `403` with the type `/problems/request.csrf_failed`.
- [ ] An unknown URL answers `404` and an unhandled exception answers `500`, both as problem details without a `type`.
- [ ] A test view decorated with `require_POST` answers a `GET` with a problem details `405` without a `type`, and the same holds for `require_GET`.
- [ ] A test fails when two apps declare the same error code.
- [ ] The old middleware, the central `ErrorCode` enum, and the `rastro_base` error and Problem classes are deleted.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
