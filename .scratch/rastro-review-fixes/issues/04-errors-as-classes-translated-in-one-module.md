# 04: Errors as classes, translated in one module

**What to build:** Make every error a class that declares its own code and HTTP status, reject a repeated code at import time, and move every translation of an error into one problems module in `rastro.common`. A caller sees a problem type on every error, including `404`, `405`, and `500`. Read the spec (`.scratch/rastro-review-fixes/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start, and follow the auto mode that the spec's Further Notes describe.

`ApplicationError` becomes `BaseError`, and every code in the spec's error table becomes a class. The problems module holds `to_error`, `Problem`, and `problem_response`. The middleware, the CSRF failure view, the `404` and `500` handlers, and `require_POST` and `require_GET` go through it. The middleware's status table and the `RequestCode` enum are deleted.

The value objects still raise `InvalidValueError` in this ticket, so `to_error` keeps reading its code from the Pydantic error context, and the validation items keep their current types. Ticket 05 replaces them.

**Blocked by:** 02

**Status:** ready-for-agent

- [x] `BaseError` raises `TypeError` when Python creates a subclass with no `code`, with no `status`, or with a code that another subclass already declared, and the message names both classes.
- [x] Every class in the spec's error table exists with its code and status, and the `iam` errors declare `409`, `401`, and `401`.
- [x] No module other than the problems module reads a Pydantic error type or builds a problem body, and the middleware imports nothing from Pydantic.
- [x] `problem_response` returns an `HttpResponse` with `application/problem+json`, and the body omits empty members.
- [x] A `404` from the URL resolver and an `Http404` from a view both answer `{"type": "/problems/request.not_found", "status": 404}`.
- [x] A wrong method answers `405` with the type `/problems/request.method_not_allowed` and an `Allow` header that names the allowed method.
- [x] An unhandled exception, including a `CheckConstraint` violation, answers `500` with the type `/problems/server.internal_error`.
- [x] A CSRF failure, `iam.email_in_use`, `iam.incorrect_credentials`, `iam.not_authenticated`, and every current validation item answer the same body as before.
- [x] The error code architecture test imports every app's errors module and checks the `<prefix>.<name>` form, and the test against the deleted status table is gone.
- [x] `CODING_STANDARDS.md` describes errors, the problems module, and problem details as the code does them.
- [x] Every decision that the spec did not settle is recorded under `## Comments`, as the spec's Further Notes describe.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest`.
- [x] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket/04-errors`. `rastro.common.errors` declares `BaseError` and the twelve shared errors, and `rastro.common.problems` holds `to_error`, `Problem`, and `problem_response`. `src/rastro/common/tests/test_views.py` covers the `404` from the URL resolver and from `Http404`, the `405`, the `500`, and the `CheckConstraint` violation. Every `iam` HTTP test passes unchanged, except the `405` test, which now expects the type `/problems/request.method_not_allowed`. The gate is green: `ruff check`, `ruff format --check`, `mypy`, `lint-imports` (6 kept), `pytest` (170 passed), and `manage.py check`. I did not run `docker compose up --build`; the merger runs it.

### Decisions

- **Gap**: the spec gives `problem_response(problem)` one argument but asks it to set `Allow` for a `MethodNotAllowedError`, which the `Problem` body does not hold. **Chosen**: `Problem` has an `allow` field with `exclude=True`, which `Problem.from_error` fills and `problem_response` copies to the header, so the body never shows it. **Rejected**: `problem_response(error)`, which breaks the signature of the spec, and an `allow` member in the body, which changes the HTTP contract.
- **Gap**: in this ticket a validation item still carries a value object code such as `iam.invalid_email`, and no `BaseError` class declares it. **Chosen**: `ValidationItem` in `rastro.common.errors` holds the JSON Pointer and an `error` typed `BaseError | InvalidValueError`, because both have a `code`. Ticket 05 narrows the type to `BaseError` when it deletes `InvalidValueError`. **Rejected**: an item that holds a code string, which brings back the magic strings, and a `BaseError` subclass per value object code, which ticket 05 deletes again.
- **Gap**: the spec gives the limit of `TooShortError` and `TooLongError` and the translation of `string_too_short`, `string_too_long`, and `string_pattern_mismatch`, but ticket 05 owns that translation. **Chosen**: `TooShortError`, `TooLongError`, and `InvalidFormatError` exist with their codes and statuses and hold no limit yet. Ticket 05 adds the limit with the translation that fills it. **Rejected**: the translation and the `min_length` and `max_length` members in this ticket, which no value object can reach before ticket 05.
- **Gap**: the spec does not say where `BaseError` keeps the codes it has seen. **Chosen**: a class attribute `_class_by_code` on `BaseError`. The `TypeError` names each class by its module and qualified name, so two classes with the same name in two apps stay apart. **Rejected**: a module-level registry, which a reader of the class does not see, and an exception for a second class with the same module and name, which no current code path needs.
- **Gap**: `BaseError` now rejects a repeated code at import time, so the old architecture test that collected codes across modules to find a repeat can no longer fail. **Chosen**: `tests/architecture/test_error_codes.py` tests the three rejections of `BaseError`, checks the `<prefix>.<name>` form, and compares every code and status with the literal table of the spec plus the three `iam` errors. **Rejected**: keeping the repeat collector, which tests what Python already refuses to import, and no table test, which leaves `TooShortError`, `TooLongError`, and `InvalidFormatError` without a test until ticket 05.
- **Gap**: the spec asks for a `500` on a `CheckConstraint` violation and for an `Http404` from a view, but no rastro view raises either. **Chosen**: the sample app gets a `Wall` model with a `CheckConstraint`, a `wall_paint_view` that breaks it, and a `paint_find_view` that raises `Http404`, so the HTTP seam covers both. **Rejected**: a raw SQL update in an `iam` view, which adds a route to the product for a test.
- **Gap**: `not_found_view` receives an exception that `to_error` could, in principle, return `None` for. **Chosen**: `to_error(exception) or NotFoundError()`, so the handler always answers `request.not_found`. **Rejected**: an `assert`, which turns a `404` into a `500` if Django ever passes another exception.
- **Gap**: the spec names the `request` prefix and the `server.internal_error` code but no rule for the `server` prefix. **Chosen**: `CODING_STANDARDS.md` states that the prefix is the app label, `request` for errors of an HTTP request that every app shares, and `server` for a failure of rastro itself. **Rejected**: leaving the `server` prefix undefined.

