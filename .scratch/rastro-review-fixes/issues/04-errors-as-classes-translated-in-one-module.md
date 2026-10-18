# 04: Errors as classes, translated in one module

**What to build:** Make every error a class that declares its own code and HTTP status, reject a repeated code at import time, and move every translation of an error into one problems module in `rastro.common`. A caller sees a problem type on every error, including `404`, `405`, and `500`. Read the spec (`.scratch/rastro-review-fixes/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start, and follow the auto mode that the spec's Further Notes describe.

`ApplicationError` becomes `BaseError`, and every code in the spec's error table becomes a class. The problems module holds `to_error`, `Problem`, and `problem_response`. The middleware, the CSRF failure view, the `404` and `500` handlers, and `require_POST` and `require_GET` go through it. The middleware's status table and the `RequestCode` enum are deleted.

The value objects still raise `InvalidValueError` in this ticket, so `to_error` keeps reading its code from the Pydantic error context, and the validation items keep their current types. Ticket 05 replaces them.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] `BaseError` raises `TypeError` when Python creates a subclass with no `code`, with no `status`, or with a code that another subclass already declared, and the message names both classes.
- [ ] Every class in the spec's error table exists with its code and status, and the `iam` errors declare `409`, `401`, and `401`.
- [ ] No module other than the problems module reads a Pydantic error type or builds a problem body, and the middleware imports nothing from Pydantic.
- [ ] `problem_response` returns an `HttpResponse` with `application/problem+json`, and the body omits empty members.
- [ ] A `404` from the URL resolver and an `Http404` from a view both answer `{"type": "/problems/request.not_found", "status": 404}`.
- [ ] A wrong method answers `405` with the type `/problems/request.method_not_allowed` and an `Allow` header that names the allowed method.
- [ ] An unhandled exception, including a `CheckConstraint` violation, answers `500` with the type `/problems/server.internal_error`.
- [ ] A CSRF failure, `iam.email_in_use`, `iam.incorrect_credentials`, `iam.not_authenticated`, and every current validation item answer the same body as before.
- [ ] The error code architecture test imports every app's errors module and checks the `<prefix>.<name>` form, and the test against the deleted status table is gone.
- [ ] `CODING_STANDARDS.md` describes errors, the problems module, and problem details as the code does them.
- [ ] Every decision that the spec did not settle is recorded under `## Comments`, as the spec's Further Notes describe.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
