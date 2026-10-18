# Fix what the review of the rastro rewrite found

Status: ready-for-agent

## Problem Statement

The rewrite in `.scratch/rastro-rewrite/spec.md` shipped, and its review found code that a developer would not want to copy. rastro exists to be copied, so each of these problems spreads to every project that copies it:

- Error codes are magic strings. The middleware repeats `"iam.email_in_use"` in a status table, and each value object raises `InvalidValueError("iam.invalid_email")` with the code typed inline.
- The translation of errors is spread over four places: the middleware, the shared views, the API helpers, and the model fields. A reader has to open all four to learn how one error becomes a response.
- Only an architecture test guards the uniqueness of error codes. The old `enum.unique` failed at import time. The test fails only when someone runs it.
- Value objects avoid Pydantic, so `StrValueObject` needs a hand-written `__get_pydantic_core_schema__`, and every edge calls `parse_value_object(Email, email)` even though Pydantic already parses the value.
- The value object rules are imperative `__post_init__` code. The pre-rewrite rules were declarative `StringConstraints`.
- The tests are hard to read. `_start_session` exists four times with four signatures, URL constants repeat in six files, and the `identity` fixture lives in the root `conftest.py`, far from `iam`.
- The view modules are named `apis.py`, which breaks the Django convention of `views.py`.
- An Output schema copies each field of the model by hand.

## Solution

Value objects become frozen Pydantic `RootModel` classes with declarative rules, so the hand-written schema, the parse helper, and `InvalidValueError` disappear. Every error is a class that holds its own code and HTTP status. The base class rejects a repeated code at import time, as `enum.unique` did. One module in `rastro.common`, the problems module, is the anti-corruption layer: it alone turns a foreign error (Pydantic, Django) into a rastro error and a rastro error into an RFC 9457 response. Every other module calls it.

The HTTP contract changes in two places. A validation item now names the rule that failed (`request.too_short`) in place of the value object (`iam.invalid_email`), and it carries the limit, so the frontend can say "at least 8 characters" without its own copy of the rule. A `404`, `405`, or `500` now carries a problem type of its own in place of `about:blank`.

The tests share fixtures per app, read URLs with `reverse()`, and start a Session with `force_login`. View modules become `views.py`, and Output schemas read the model with `from_attributes`.

## User Stories

### Frontend developer

1. As a frontend developer, I want each validation item to name the rule that failed, so that I can tell "too long" from "wrong format" on the same field.
2. As a frontend developer, I want a `request.too_short` item to carry `min_length`, so that I can show "at least 8 characters" without a copy of the rule.
3. As a frontend developer, I want a `request.too_long` item to carry `max_length`, so that I can show the limit next to the input.
4. As a frontend developer, I want a `request.invalid_format` item to omit the pattern, so that the response never exposes a regular expression that I would be tempted to copy.
5. As a frontend developer, I want a missing field, a wrong type, malformed JSON, and an unknown field to keep their current problem types, so that my existing error handling keeps working.
6. As a frontend developer, I want a `404` to carry the type `/problems/request.not_found`, so that every problem I receive has a type to map.
7. As a frontend developer, I want a `405` to carry the type `/problems/request.method_not_allowed` and keep its `Allow` header, so that I can see which method the URL accepts.
8. As a frontend developer, I want a `500` to carry the type `/problems/server.internal_error`, so that my error handler has no special case for a missing type.
9. As a frontend developer, I want a CSRF failure to keep the type `/problems/request.csrf_failed`, so that my CSRF retry logic keeps working.
10. As a frontend developer, I want every problem response to keep the media type `application/problem+json`, so that I can detect a problem by its header.

### API consumer

11. As an API consumer, I want the `status` inside a problem to match the response status for every error, including `404`, `405`, and `500`, so that I can log a problem on its own.
12. As an API consumer, I want every operation to keep its URL and method, so that this change breaks none of my calls.
13. As an API consumer, I want successful responses to keep their bodies and statuses, so that only the error items change.

### Maintainer of rastro

14. As a maintainer, I want each error to be a class that declares its code and its HTTP status, so that one class tells me everything about one error.
15. As a maintainer, I want an error code to appear as a string exactly once, in the class that declares it, so that no magic string spreads through the code.
16. As a maintainer, I want the base error class to raise at import time when two classes declare the same code, so that a collision fails as early as `enum.unique` did.
17. As a maintainer, I want the base error class to reject a subclass without a code or without a status, so that no error reaches a response half-declared.
18. As a maintainer, I want every shared code (`request.*` and `server.*`) to be a class too, so that the CSRF view, the handlers, and the middleware name a class in place of a string.
19. As a maintainer, I want one module to translate every foreign error into a rastro error, so that I read one file to learn how Pydantic and Django errors become problems.
20. As a maintainer, I want the same module to turn a rastro error into a problem response, so that the response format has one implementation.
21. As a maintainer, I want the middleware to call the problems module and import nothing from Pydantic, so that the middleware stays three lines of dispatch.
22. As a maintainer, I want the model fields and the admin to take their error codes from the problems module, so that the admin and the API report the same code for the same mistake.
23. As a maintainer, I want value objects to declare their rules with `StringConstraints`, so that I read a rule in one line.
24. As a maintainer, I want value objects to be frozen Pydantic `RootModel` classes, so that a schema field typed `Email` parses and serializes without adapter code.
25. As a maintainer, I want `StrValueObject`, `__get_pydantic_core_schema__`, `parse_value_object`, and `InvalidValueError` removed, so that nobody copies adapter code that Pydantic makes unnecessary.
26. As a maintainer, I want an edge to parse a raw value with `model_validate`, so that an edge accepts either a raw string or a value object without a helper.
27. As a maintainer, I want mypy to keep rejecting a raw `str` or the wrong value object in a service argument, so that the move to Pydantic keeps the type safety of the dataclasses.
28. As a maintainer, I want a value that the database returns and that fails its value object to keep raising, so that corrupted data stays visible.
29. As a maintainer, I want an Output schema to read a model with `from_attributes`, so that a new output field is declared once.
30. As a maintainer, I want an Output field with a name different from the model attribute to use `validation_alias`, and a nested attribute to use `AliasPath`, so that renames stay declarative.
31. As a maintainer, I want a computed output value to come ready from the selector, so that schemas hold no logic.
32. As a maintainer, I want the view modules named `views.py` and the view functions named `<entity>_<action>_view`, so that rastro follows the Django convention.
33. As a maintainer, I want the shared view helpers to live in `rastro.common`'s views module, so that every view import comes from one place.
34. As a maintainer, I want every URL pattern to have a name inside an app namespace, so that tests and code build URLs with `reverse()`.
35. As a maintainer, I want the Identity to keep `AbstractBaseUser`, so that Django's checks for timing, hash upgrades, and Session hashes stay Django's responsibility.

### Developer who copies the pattern

36. As a developer who copies the pattern, I want `CODING_STANDARDS.md` to describe errors, problems, value objects, views, and tests as the code does them, so that I can copy either one.
37. As a developer who copies the pattern, I want ADR 0001 to record why value objects use Pydantic and why errors carry their status, so that nobody reverts the choice without the reasons.
38. As a developer who copies the pattern, I want a new error to need one class and nothing else, so that I add an error without editing a table.

### Agent that implements a ticket

39. As an agent, I want an architecture test to reject a Pydantic error type outside the problems module and the fields module, so that I cannot spread the translation again.
40. As an agent, I want the import contracts to allow Pydantic in `values` and to keep banning it in `services` and `selectors`, so that I know where parsing happens.
41. As an agent, I want `CODING_STANDARDS.md` to tell me to look for and plan reusable fixtures before I write a test, so that I extend the shared fixtures in place of a new private helper.
42. As an agent, I want every check in the README to pass at the end of each ticket, so that I can tell a finished ticket from an unfinished one.

### Person who writes a test

43. As a person who writes a test, I want an `identity` fixture in the `iam` test package, so that the state that most tests need takes one argument.
44. As a person who writes a test, I want a `signed_in_client` fixture that builds on `identity`, so that a test of a Session-only view needs no setup code.
45. As a person who writes a test, I want fixtures for the fake Session store and the fake password hasher, so that a service test asks for its fakes by name.
46. As a person who writes a test, I want an `admin_client` fixture in the `iam` test package, so that every admin test shares one administrator setup.
47. As a person who writes a test, I want a variation of the shared state, for example a second email, to call the factory in the test, so that the fixture set stays small.
48. As a person who writes a test, I want HTTP tests to compare the literal JSON of a problem, so that a change to an error code breaks a test.
49. As a person who writes a test, I want service tests to assert the error class with `pytest.raises`, so that a service test reads in the domain language.
50. As a person who writes a test, I want to post JSON with the Django test client and `content_type="application/json"`, so that no test file needs a private post helper.
51. As a person who writes a test, I want test classes to be optional, so that I group tests in a class only when the grouping helps the reader.

### Administrator

52. As an administrator, I want the Django admin to keep rejecting an invalid email on the email field, so that the admin cannot store invalid data.
53. As an administrator, I want the admin to reject a short password on the password field, so that I see the error next to the input.
54. As an administrator, I want `createsuperuser` to keep applying the registration rules, so that an administrator follows the same rules as everyone else.

## Implementation Decisions

### Value objects

- The value object base in `rastro.common` is a `RootModel` subclass whose only content is `frozen=True`. It has no `value` alias, so code reads a value through `.root`.
- Each value object declares its rules with `Annotated` and `StringConstraints`. A rule that `StringConstraints` cannot express, such as NFKC normalization, uses a `BeforeValidator` that only transforms and never raises.
- The `iam` value objects keep their current rules: `Email` strips, applies NFKC, lowercases, allows at most 254 characters, and matches rastro's pattern. `DisplayName` strips and allows at most 320 characters. `RawPassword` keeps spaces and requires at least 8 characters. `HashedPassword` has no rule.
- A prototype confirmed the shape and the behaviour with Pydantic 2.13.4: `Email(" Ａna@X.com ")` gives `Email(root='ana@x.com')`, a schema field typed `Email` parses JSON, and mypy rejects `email=DisplayName(...)` and `email="a@x.com"` in a service call. The declaration from the prototype:

  ```python
  class Email(ValueObject[Annotated[
      str,
      BeforeValidator(_nfkc),
      StringConstraints(
          strip_whitespace=True, to_lower=True, max_length=254, pattern=EMAIL_PATTERN
      ),
  ]]):
      pass
  ```

- `StrValueObject`, its `__get_pydantic_core_schema__`, `parse_value_object`, `InvalidValueError`, and every `iam.invalid_*` code are deleted.
- An edge parses a raw value with `<ValueObject>.model_validate(value)`, which accepts a raw string or an instance of the value object.
- An `Id` value object is out of this spec. It arrives with the first service or selector that receives an id.

### Errors

- `ApplicationError` is renamed `BaseError`. A subclass declares two class attributes: `code`, a string of the form `<prefix>.<name>`, and `status`, an `HTTPStatus`.
- `BaseError` checks each subclass when Python creates it. It raises `TypeError` when the subclass declares no `code` or no `status`, and when another subclass already declared the same `code`. The message names both classes.
- Every error class name ends in `Error`, as PEP 8 recommends.
- The shared errors live in `rastro.common`'s errors module, and the `RequestCode` enum is deleted:

  | Class | Code | Status |
  |---|---|---|
  | `ValidationFailedError` | `request.validation_failed` | `422` |
  | `FieldRequiredError` | `request.field_required` | `422` |
  | `InvalidTypeError` | `request.invalid_type` | `422` |
  | `InvalidJsonError` | `request.invalid_json` | `422` |
  | `UnknownFieldError` | `request.unknown_field` | `422` |
  | `TooShortError` | `request.too_short` | `422` |
  | `TooLongError` | `request.too_long` | `422` |
  | `InvalidFormatError` | `request.invalid_format` | `422` |
  | `CsrfFailedError` | `request.csrf_failed` | `403` |
  | `NotFoundError` | `request.not_found` | `404` |
  | `MethodNotAllowedError` | `request.method_not_allowed` | `405` |
  | `InternalServerError` | `server.internal_error` | `500` |

- A field error (the `422` classes other than `ValidationFailedError`) uses the same base. Its status never reaches a response, because only the outer `request.validation_failed` problem shows a status.
- `ValidationFailedError` holds one item per failed field. An item holds the JSON Pointer, the field error, and the limit for `TooShortError` and `TooLongError`.
- `MethodNotAllowedError` holds the method that the URL allows, so that the response can set the `Allow` header.
- The `iam` errors keep their codes and gain a status: `EmailInUseError` (`409`), `IncorrectCredentialsError` (`401`), and `NotAuthenticatedError` (`401`).

### The problems module

- One module in `rastro.common`, the problems module, is the only translation layer in rastro. No other module reads a Pydantic error type or builds a problem body.
- `to_error(exception)` turns an exception into a `BaseError` or `None`. It returns a `BaseError` unchanged, turns a `pydantic.ValidationError` into a `ValidationFailedError`, turns `Http404` into `NotFoundError`, and returns `None` for anything else.
- The translation of Pydantic error types lives in one table in this module: `missing` becomes `FieldRequiredError`, `json_invalid` becomes `InvalidJsonError`, `extra_forbidden` becomes `UnknownFieldError`, `string_too_short` becomes `TooShortError`, `string_too_long` becomes `TooLongError`, `string_pattern_mismatch` becomes `InvalidFormatError`, and any other type becomes `InvalidTypeError`. The limit comes from the `ctx` of the Pydantic error.
- `Problem` is a Pydantic model with `type`, `status`, and an optional `errors` list. `Problem.from_error(error)` builds it from a `BaseError`. The `type` is `/problems/<code>`.
- `problem_response(problem)` returns an `HttpResponse` with the same shape as `respond`: the body is `problem.model_dump_json(exclude_none=True)`, the status is `problem.status`, and the content type is `application/problem+json`. For a `MethodNotAllowedError`, the response also sets `Allow`.
- A validation failure keeps the current body shape and adds the limit to `too_short` and `too_long` items:

  ```json
  {
    "type": "/problems/request.validation_failed",
    "status": 422,
    "errors": [
      {"pointer": "#/email", "type": "/problems/request.invalid_format"},
      {"pointer": "#/password", "type": "/problems/request.too_short", "min_length": 8}
    ]
  }
  ```

### Callers of the problems module

- The middleware calls `to_error`, returns `None` when the result is `None`, and otherwise returns `problem_response(Problem.from_error(error))`. It imports nothing from Pydantic. The status table in the middleware is deleted.
- The CSRF failure view answers `CsrfFailedError`. The `404` handler passes its exception through `to_error`, so a `404` from the URL resolver and an `Http404` from a view answer the same problem. The `500` handler answers `InternalServerError`.
- `require_POST` and `require_GET` raise `MethodNotAllowedError`, and the middleware answers it like any other error.
- An unhandled exception, including a `CheckConstraint` violation, still answers `500`.
- The fields module in `rastro.common` holds the model field for value objects and a form field for value objects. Both parse with `model_validate`, pass a failure through `to_error`, and raise Django's `ValidationError` with the code of each field error, so the admin shows the error on its field.
- The admin add form uses the value object form field for the password, so the admin catches no Pydantic error itself.
- The Identity manager's `create_user` and `create_superuser` parse with `model_validate` and call the services, as today.

### Views and schemas

- Each app's view module is `views.py`, and each view function is `<entity>_<action>_view`, for example `session_start_view`.
- `parse_body`, `respond`, `require_POST`, and `require_GET` move from `rastro.common`'s API module into its views module, which already holds the CSRF failure view and the handlers. The API module is deleted.
- Each URLconf of an app sets `app_name`, and each URL pattern has a name, so `reverse("iam:session_start")` resolves.
- An Output schema sets `from_attributes=True`, and its view builds it with `<Output>.model_validate(model)`. A field whose name differs from the model attribute uses `Field(validation_alias=...)`, and a nested attribute uses `AliasPath`. A computed value comes ready from the selector.
- The HTTP contract keeps every URL, method, and success response of `.scratch/rastro-rewrite/spec.md`.

### The Identity model

- `Identity` keeps `AbstractBaseUser` and `PermissionsMixin`, and no check bans `set_password` or `check_password`. Django's `ModelBackend` calls `set_password` on a blank Identity to equalize timing for an unknown email, so a model without `AbstractBaseUser` would need a backend that rastro owns.

### Architecture checks

- The import contract for `values` allows the standard library, `pydantic`, and `rastro.common`'s values module.
- `services` and `selectors` still import neither `pydantic` nor `django.conf`.
- A new pytest architecture test checks that only the problems module and the fields module import `pydantic.ValidationError` or `pydantic_core`. import-linter cannot name a submodule of an external package, so pytest checks it.
- The error code test imports every `<app>.errors` module, so that `BaseError`'s check runs for every app, and it checks the `<prefix>.<name>` form. The test that compares codes with the middleware's status table is deleted with the table.
- Every reference to `apis` in the import contracts and the architecture tests becomes `views`.

### Documentation

- ADR 0001 is rewritten to record the current decision: the core couples to Django, value objects are Pydantic models, every error carries its code and status, and one module translates foreign errors.
- `CODING_STANDARDS.md` changes in the same ticket as the code it describes. Its sections on value objects, errors and problem details, APIs (renamed views), architecture checks, and tests follow this spec.
- The test section of `CODING_STANDARDS.md` tells an agent to look in the app's `conftest.py` for a fixture that builds the state a test needs before it writes the test, and to add a fixture when two tests need the same state.

## Testing Decisions

### What makes a good test

- A good test exercises behaviour through a public seam and asserts what a caller observes: an HTTP status, a response body, a header, a cookie, a raised error, or the state of the database.
- A test that breaks when a private helper is renamed or a module is reorganized tests the implementation, and is rewritten.
- A service test passes fakes as arguments. Nothing uses `mock.patch`.
- An HTTP test compares the literal JSON of a problem, because the literal is the contract. A service test asserts the error class.

### Seams

The user confirmed the four seams of the previous spec, with no new seam:

1. **The HTTP seam** is the primary seam. Tests use Django's test `Client` against the test database. They cover every problem type in the error table, the `min_length` and `max_length` members, the `Allow` header of a `405`, the `404` from the URL resolver and from `Http404`, the `500`, the CSRF failure, the admin errors on the email and password fields, and `createsuperuser` through `call_command`. The problems module, the middleware, and the fields get no seam of their own, because every translation passes through this seam.
2. **The service and selector seam** keeps its tests, rewritten to take the fakes from fixtures.
3. **The value object seam** is pure and uses no database. It covers normalization and rejection of each value object. The code of a rejection belongs to the HTTP seam.
4. **The architecture seam** covers `BaseError`'s rejection of a repeated code, a missing code, and a missing status, the new check on Pydantic error types, and the existing import and signature rules.

### Fixtures

- Each app's test package has a `conftest.py` with the fixtures that more than one test of the app uses. For `iam`, these are `identity`, `signed_in_client`, `admin_client`, `session_store`, and `password_hasher`.
- A fixture used by more than one app lives in the root `conftest.py`. The `identity` fixture moves out of it.
- A test that needs a variation of the shared state calls the factory itself.
- `force_login` starts a Session in every test except the tests of `session_start`, which go through the view.
- URLs come from `reverse()`. The private helpers `_start_session`, `_post`, `_register`, and `_post_json`, and the URL constants, are deleted.
- Test classes are optional.

### Prior art

- The existing HTTP tests in the `iam` test package show the status and body assertions. Their contract assertions stay, and their setup moves to fixtures.
- The existing admin test shows how to read a field error from the admin form context.
- The existing architecture tests show the AST checks that the new Pydantic check follows.

## Out of Scope

- A model for Identity without `AbstractBaseUser`, and any check on `set_password`.
- The `Id` value object.
- Value object rules that `StringConstraints` cannot express, such as a CPF check digit. The first value object that needs one decides how it reports its code.
- Any change to URLs, methods, or success responses.
- A check for a repeated URL name. Django lets `reverse()` return the last pattern with the name and warns about nothing, and rastro accepts that.
- Generating schemas from models (django-ninja `ModelSchema`, djantic) and replacing the Django ORM with SQLModel.
- Everything that `.scratch/rastro-rewrite/spec.md` puts out of scope.

## Further Notes

- The grilling session settled every decision here. An agent implements the tickets in auto mode and never stops to ask the user. When a ticket finds a gap, the agent picks the option that fits this spec, `CODING_STANDARDS.md`, and ADR 0001 best, applies it, updates `CODING_STANDARDS.md` in the same change, and records the decision under a `Decisions` heading in the ticket's `## Comments`. Each record names the gap, the option chosen, and the options rejected.
- At the end of `implement-spec`, the agent reports every recorded decision of every ticket to the user for review, grouped by ticket.
- The HackSoft Django Styleguide shows `given_a_user(...)` in one service test example but never defines it. rastro takes the idea of reusable setup and builds it with pytest fixtures.
- The change to the validation items breaks the frontend contract of `.scratch/rastro-rewrite/spec.md`. The user confirmed that no frontend reads the old item types, so the change ships with no transition period.
