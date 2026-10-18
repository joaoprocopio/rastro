# Rewrite rastro to the patterns in CODING_STANDARDS.md

Status: ready-for-agent

## Problem Statement

rastro exists to define patterns that other Django projects copy, but its current shape makes it a poor example to copy. It splits the `iam` context into DDD layers (domain, application, infrastructure, presentation) and keeps an Identity in four shapes: the ORM model, the aggregate, an output DTO, and a public DTO. One login request changes the shape of its data about 8 times, and the same field list is written about 5 times. The copies have already drifted apart: three different rules normalize an email address, so `Foo@Bar.com` becomes `foo@bar.com` on one path and `Foo@bar.com` on another.

The cost is high for every person who touches the code. A maintainer pays it in mappers and DTOs for every field change. A developer who copies the pattern inherits ceremony with no payoff. An agent that implements a ticket has to keep four representations in sync. Meanwhile, the layers hide real defects:

- A duplicate email answers `500`.
- A login for an unknown email answers faster than a login with a wrong password, so a caller can tell which emails exist.
- The aggregate's `last_login` is stale after a login.
- `GET /session` without a Session answers a bare `401` with no body.
- Telemetry records the email of the Identity and the SQL parameters, which include password hashes.
- `createsuperuser` cannot create an Identity, because the model does not require `display_name`.

## Solution

Rewrite the whole project to the rules in `CODING_STANDARDS.md` and the decision in `docs/adr/0001-django-coupled-services-and-selectors.md`. The core couples to the Django ORM and follows the HackSoft Django Styleguide: services write, selectors read, and the Django model is the only representation of an Identity. Three ideas from the old design stay, in a lighter form:

- **Validation lives only at the edges**, in framework-free value objects. Services and selectors accept only value objects.
- **Every dependency is explicit**: a required, keyword-only argument typed with a `Protocol`, with the real implementation chosen in one `deps` module per app.
- **The domain language** in `GLOSSARY.md` names the code: Identity, Credentials, Session.

The HTTP contract changes on purpose. Commands answer with no body, queries answer with data, and every error is an RFC 9457 problem details object that carries only `type` and `status`, so a frontend or an API consumer can map each problem type to its own message. Tools check the architecture rules, so a violation fails a check instead of waiting for a review.

## User Stories

### Person who uses rastro

1. As a person, I want to register an Identity with my email address, a display name, and a password, so that I can use rastro.
2. As a person, I want registration to accept my email with surrounding spaces or capital letters, so that `" Ana@X.com "` and `ana@x.com` reach the same Identity.
3. As a person, I want registration to treat full-width characters as their plain form, so that `ａｎａ@x.com` and `ana@x.com` are the same Identity.
4. As a person, I want registration to keep my password exactly as I typed it, including spaces, so that the password I chose is the one that works.
5. As a person, I want registration to reject a password shorter than 8 characters, so that my account has a minimum of protection.
6. As a person, I want registration to tell me that my email is already in use, so that I know to start a Session instead.
7. As a person, I want registration to leave me without a Session, so that I start a Session with my Credentials as a separate step.
8. As a person, I want to start a Session with my Credentials, so that rastro knows who I am on later requests.
9. As a person, I want one answer for both an unknown email and a wrong password, so that nobody learns which emails have an Identity.
10. As a person, I want a Session start for an unknown email to take as long as one for a wrong password, so that response time does not reveal which emails exist.
11. As a person, I want a Session start to be refused when my Identity is inactive, so that a deactivated Identity cannot act.
12. As a person, I want to start a Session again while I already have one, so that a repeated request does not fail.
13. As a person, I want to see the Identity of my current Session, so that the frontend can show who is signed in.
14. As a person without a Session, I want a clear "not authenticated" problem when I ask for the current Session, so that the frontend can send me to the Session start.
15. As a person, I want to end my Session, so that nobody can act as me on this device.
16. As a person, I want ending a Session that does not exist to succeed, so that a repeated request does not fail.
17. As a person, I want my old password hash to upgrade when I start a Session, so that my stored password uses the current algorithm without any action from me.

### Frontend developer

18. As a frontend developer, I want the frontend to run no validation of its own, so that each rule has one implementation, in the backend.
19. As a frontend developer, I want every validation error to point at its field with a JSON Pointer, so that I can show the message next to the right input.
20. As a frontend developer, I want every error to carry a stable problem type, so that I can choose and translate the text myself.
21. As a frontend developer, I want every validation error in a request reported at once, so that a person fixes every field in one pass.
22. As a frontend developer, I want a missing field, a wrong type, malformed JSON, and an unknown field to have rastro's own problem types, so that the contract does not change if the backend replaces Pydantic.
23. As a frontend developer, I want an endpoint that sets the CSRF cookie, so that a single-page app can read the token and send it in the `X-CSRFToken` header.
24. As a frontend developer, I want the CSRF cookie to be readable from JavaScript, so that the single-page app can send the token.
25. As a frontend developer, I want a CSRF failure to answer with problem details, so that my error handling has one format.
26. As a frontend developer, I want a `404`, a `405`, and a `500` to answer with problem details too, so that I never parse an HTML error page.
27. As a frontend developer, I want commands to answer with no body, so that I always read data through a query.

### API consumer

28. As an API consumer, I want each problem type to be a URI under `/problems/`, so that a future documentation page can live at that URI without a change to the identifier.
29. As an API consumer, I want the HTTP status inside the problem to match the response status, so that I can log the problem on its own.
30. As an API consumer, I want each operation to have its own URL that names the action, so that I can tell a command from a query by its URL and method.
31. As an API consumer, I want no response to expose an id, so that I cannot enumerate Identities.

### Administrator

32. As an administrator, I want `createsuperuser` to ask for the email, the display name, and the password, so that I can create the first administrator.
33. As an administrator, I want `createsuperuser` to apply the same email and password rules as registration, so that an administrator follows the same rules as everyone else.
34. As an administrator, I want the Django admin to reject an invalid email and show the error on the field, so that the admin cannot store invalid data.
35. As an administrator, I want the Django admin to manage Identities, so that I can deactivate one or grant staff access.

### Maintainer of rastro

36. As a maintainer, I want one representation of an Identity, the Django model, so that a field change touches one class and its value object.
37. As a maintainer, I want each validation rule in exactly one value object, so that a rule change is a one-place edit.
38. As a maintainer, I want value objects to import no framework, so that the rules stay readable and portable.
39. As a maintainer, I want enums to be plain `StrEnum` classes, so that Django's `TextChoices` stays out of the core.
40. As a maintainer, I want a model field to return a value object when Django reads from the database, so that the core never sees a raw string.
41. As a maintainer, I want a value that the database returns and that fails its value object to raise, so that corrupted data is visible at once.
42. As a maintainer, I want services to receive every dependency as a required argument, so that mypy lists every caller that a new dependency affects.
43. As a maintainer, I want every real implementation chosen in one `deps` module per app, so that swapping SMTP for SES, or one auth provider for another, is a one-line change.
44. As a maintainer, I want each implementation to carry a line that checks it against its protocol, so that mypy rejects an adapter with the wrong shape.
45. As a maintainer, I want only adapters to read settings, so that services stay free of configuration.
46. As a maintainer, I want error codes declared per app with the form `<app>.<name>`, so that each context owns its errors.
47. As a maintainer, I want a test that rejects a repeated error code across apps, so that two problem types never collide.
48. As a maintainer, I want one table that maps error codes to HTTP statuses, so that services carry no HTTP knowledge.
49. As a maintainer, I want a race between two registrations with the same email to answer "email in use", so that a concurrent request never causes a `500`.
50. As a maintainer, I want a `CheckConstraint` violation to answer `500`, so that a bug in an edge is never disguised as a person's mistake.
51. As a maintainer, I want every write service wrapped in a transaction, so that a failure leaves no partial write.
52. As a maintainer, I want settings split into a base module, a test module, and one module per integration, so that I can find each setting fast.
53. As a maintainer, I want `DEBUG` to default to off and `SECRET_KEY` to be required when `DEBUG` is off, so that a missing variable never runs production in debug mode.
54. As a maintainer, I want each setting defined once, so that no later line silently overrides an earlier one.
55. As a maintainer, I want the old DDD packages and base classes removed, so that nobody copies a pattern that rastro no longer uses.
56. As a maintainer, I want the README and `CLAUDE.md` to describe the new architecture, so that a new reader learns the current pattern.

### Developer who copies the pattern

57. As a developer who copies the pattern, I want every rule in `CODING_STANDARDS.md` to match the code, so that I can copy either one.
58. As a developer who copies the pattern, I want the rules checked by tools, so that my project inherits the checks along with the rules.
59. As a developer who copies the pattern, I want `rastro/common` to hold every reusable building block, so that I can copy one package into a new project.

### Agent that implements a ticket

60. As an agent, I want a fixed set of check commands, so that I can tell a finished ticket from an unfinished one.
61. As an agent, I want import contracts to reject a forbidden import, so that I learn about a layer violation at once.
62. As an agent, I want architecture tests to reject a service with a raw `str` argument, a dependency default, or a return value, so that I cannot drift from the pattern unnoticed.

### Operator who watches Grafana

63. As an operator, I want spans to carry only the Identity's id, never its email, so that telemetry holds no personal data.
64. As an operator, I want SQL spans to omit query parameters, so that password hashes never reach ClickHouse.
65. As an operator, I want the ASGI entry point and `manage.py` instrumented as well as WSGI, so that every way of running rastro produces telemetry.
66. As an operator, I want `docker compose up --build` to keep working after every ticket, so that the full stack is always runnable.

## Implementation Decisions

### Project structure

- The `rastro` package holds only the Django project wiring: the settings package, the root URLconf, the WSGI and ASGI entry points, and the telemetry setup.
- A new `rastro.common` package holds every building block that more than one app uses. It replaces `rastro_base` and `rastro_shared_kernel`, which are deleted with all their base classes (`Entity`, `AggregateRoot`, `ValueObject`, `RootValueObject`, `DTO`, `Mapper`, `UseCase`, `Service`, `BaseError`).
- `rastro.common` holds:
  - the value object base `StrValueObject` and `InvalidValueError`, a `ValueError` subclass that carries a code;
  - model field adapters, including the generic `StrEnumField`;
  - the abstract `BaseModel` with `created_at` and `updated_at`;
  - `ApplicationError`;
  - the problem details middleware, the CSRF failure view, and the 404 and 500 handlers;
  - the API helpers: `parse_body`, `respond`, `require_POST`, and `require_GET`;
  - the environment helpers `get_env`, `parse_csv`, `parse_booleanish`, and `str_enum_to_choices`;
  - shared adapters, in a subpackage.
- The `iam` app uses the flat layout from `CODING_STANDARDS.md`: models, values, errors, ports, adapters, deps, services, selectors, schemas, apis, urls, admin, and a tests package. The `domain`, `application`, `infrastructure`, `presentation`, and `shared` subpackages are deleted.
- `rastro/codes.py` and its central `ErrorCode` enum are deleted.

### Value objects in iam

- `Email`: strips spaces, applies Unicode NFKC normalization, lowercases the whole address, and checks the format with rastro's own pattern. Code `iam.invalid_email`.
- `DisplayName`: strips spaces and allows at most 320 characters. Code `iam.invalid_display_name`.
- `RawPassword`: keeps spaces and requires at least 8 characters. Code `iam.invalid_password`.
- `HashedPassword`: wraps the stored hash. It has no format rule.
- Each value object is a frozen, slotted dataclass that subclasses `StrValueObject`, and the code reads it through `.value`.

### The Identity model

- The model is named `Identity`, and its table is `iam_identity`.
- It subclasses `BaseModel`, `AbstractBaseUser`, and `PermissionsMixin`. `PermissionsMixin` stays because the Django admin needs it.
- Fields:
  - `email`, through an iam-specific field adapter that converts to and from `Email` and turns `InvalidValueError` into Django's `ValidationError` for the admin;
  - `display_name`, through an adapter for `DisplayName`;
  - the password hash, `is_active`, `is_staff`, `last_login`, `created_at`, and `updated_at`.
- The `date_joined` field is removed, because `created_at` replaces it.
- Constraints: `email` is unique, and a `CheckConstraint` requires `email` to equal its lowercase form.
- `USERNAME_FIELD` is `email`, and `REQUIRED_FIELDS` includes `display_name`, so that `createsuperuser` asks for it.
- The existing migrations are deleted and replaced with a new initial migration. No production data exists.

### The Identity manager

- The manager holds only `create_user` and `create_superuser`, because `createsuperuser` requires them.
- Both methods are edges. Each one parses its raw arguments into value objects, calls the matching service with the implementations from `deps`, and reads the Identity back to return it, because `createsuperuser` expects a return value.
- The code that the old manager copied from Django's `UserManager` is removed: `_create_user`, `_create_user_object`, `normalize_email`, `make_password`, `with_perm`, the `alters_data` markers, and `use_in_migrations`.

### Ports, adapters, and deps in iam

- `Authenticator` checks Credentials and returns the matching active Identity or `None`. The Django adapter uses `django.contrib.auth.authenticate`, which hashes a password even for an unknown email (so that the response time stays equal), upgrades an outdated hash, and refuses an inactive Identity.
- `SessionStore` starts a Session for an Identity, ends the current Session, and returns the Identity of the current Session or `None`. Every method receives the request. The Django adapter uses `login`, `logout`, and `get_user`. Because the Identity is the real model, Django's `last_login` update applies to it.
- `PasswordHasher` turns a `RawPassword` into a `HashedPassword`. The Django adapter uses the configured password hashers.
- Each adapter has a line below its definition that assigns it to its protocol, so that mypy checks the shape.
- The `deps` module holds one constant per port with the real implementation. It holds no factories, containers, or logic.

### Services and selectors in iam

- `identity_register` takes `email`, `display_name`, `password`, and `password_hasher`. It raises `EmailInUseError` when the email is in use. It also catches the `IntegrityError` that a concurrent registration can cause and raises the same error. It returns `None`.
- `identity_register_superuser` takes the same arguments and also sets `is_staff` and `is_superuser`. Deciding who is an administrator is a business rule, so it lives here and not in the manager.
- `session_start` takes `request`, `email`, `password`, `authenticator`, and `session_store`. It raises `IncorrectCredentialsError` when the authenticator returns `None`, and it starts the Session otherwise.
- `session_end` takes `request` and `session_store`. It succeeds whether or not a Session exists.
- The selector `identity_get_current` takes `request` and `session_store`. It returns the Identity of the current Session and raises `NotAuthenticatedError` when there is none.
- Every service that writes runs in a transaction. Every argument is keyword-only and typed, and every dependency argument is required.

### Errors in iam

- `iam.email_in_use` answers `409`.
- `iam.incorrect_credentials` answers `401`.
- `iam.not_authenticated` answers `401`.
- `iam.invalid_email`, `iam.invalid_display_name`, and `iam.invalid_password` appear as items of a `request.validation_failed` problem.

### HTTP contract

All URLs live under `/api/v1/iam/`. A command uses `POST` on a URL that names the action. A query uses `GET`. Each operation is one view function named `<entity>_<action>_api`, and no API is exempt from CSRF.

| Operation | Method and URL | Input | Success |
|---|---|---|---|
| Register an Identity | `POST /api/v1/iam/identities/register` | `email`, `display_name`, `password` | `201`, no body |
| Start a Session | `POST /api/v1/iam/session/start` | `email`, `password` | `204`, no body |
| End a Session | `POST /api/v1/iam/session/end` | none | `204`, no body |
| Read the current Session | `GET /api/v1/iam/session` | none | `200` with `email` and `display_name` |
| Set the CSRF cookie | `GET /api/v1/iam/csrf` | none | `204`, sets the `csrftoken` cookie |

- The input and output schemas are Pydantic models named `<Entity><Action>Input` and `<Entity><Action>Output`. Their fields use the value object types, so a request is parsed into value objects once. Each schema serves one operation, and no operation reuses another operation's schema.
- No response contains an id.

### Problem details

- Every error response is `application/problem+json` with only `type` and `status`. The `type` is `/problems/<code>`. The response has no `title`, `detail`, or `code` member.
- An error without a code of its own omits `type`, which RFC 9457 reads as `about:blank`. This covers `404`, `405`, and `500`.
- A CSRF failure answers `403` with the type `/problems/request.csrf_failed`.
- A validation failure answers `422` with the type `/problems/request.validation_failed` and an `errors` extension. Each item has a JSON Pointer to the field and a problem type:

  ```json
  {
    "type": "/problems/request.validation_failed",
    "status": 422,
    "errors": [
      {"pointer": "#/email", "type": "/problems/iam.invalid_email"},
      {"pointer": "#/password", "type": "/problems/request.field_required"}
    ]
  }
  ```

- The middleware translates the errors that Pydantic raises before any value object runs into the shared `request.` codes:

  | Pydantic error | rastro code |
  |---|---|
  | missing field | `request.field_required` |
  | wrong type | `request.invalid_type` |
  | malformed JSON | `request.invalid_json` |
  | unknown field | `request.unknown_field` |

- The middleware reads the code of an `InvalidValueError` from the Pydantic error context.
- The middleware holds the only table that maps an error code to an HTTP status.
- An unhandled exception, including a `CheckConstraint` violation, answers `500`.

### Settings

- The settings package has four modules:
  - a base module with every setting;
  - a test module that overrides values for the test run, including a fast password hasher;
  - a telemetry module;
  - a sessions module.
- No setting exists only in production. Environment variables, read with `get_env`, switch features on and off. Every variable uses the `RASTRO_` prefix in place of today's `RASTRO_DJANGO_`, for example `RASTRO_SECRET_KEY`, and `compose.yaml` and the tests use the new names.
- `DEBUG` defaults to off. `SECRET_KEY` has no insecure default and is required when `DEBUG` is off.
- `CSRF_COOKIE_HTTPONLY` is `False` and is defined once.
- The unused `OTEL_HTTP_ENDPOINT` setting is removed.
- The test run uses the test settings module. The type checker uses the base module.

### Telemetry

- The Django instrumentation records only the Identity's id on the request span, as `enduser.id`, and never the email.
- The psycopg2 instrumentation stops capturing query parameters.
- The WSGI entry point, the ASGI entry point, and `manage.py` all call the telemetry setup.
- Spans and metrics in services and selectors are out of scope (see Out of Scope).

### Tooling

- The project adds import-linter and factory_boy and drops model_bakery.
- ruff gets a configuration that bans `django.dispatch.receiver` and `csrf_exempt` through `TID251`.
- import-linter contracts enforce the following rules:
  - the layer order `apis`, then `services` and `selectors`, then `models` and `values`, with no import upward;
  - only `apis` imports `schemas`;
  - `services` and `selectors` import neither `pydantic` nor `django.conf`;
  - `values` imports nothing outside the standard library and `rastro.common`'s value object module;
  - `services` and `selectors` import `ports` but never `adapters`;
  - only `deps` imports `adapters`.
- The check gate for every ticket is: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`, and `pytest`. All five pass at the end of every ticket.

### Documentation

- `CODING_STANDARDS.md` already holds the rules, and each ticket keeps it true. Its opening sentence about code that predates the rewrite is removed in the last ticket.
- The README describes the new architecture and the check gate. It replaces the DDD description.
- The project `CLAUDE.md` drops "structured with DDD" and describes the new pattern in one line.
- `GLOSSARY.md` stays the source of the domain terms, and ADR 0001 records the central decision.

### Order of the rewrite

- The rewrite is cut into vertical slices. Every ticket ends with the check gate passing and `docker compose up --build` serving the app. An old part is deleted in the same ticket that replaces it, so the old and the new code never answer the same request.
- The first ticket builds the foundation: `rastro.common`, the settings package, the problem details middleware, and the tooling, including the import contracts and the architecture tests. Each later ticket rewrites one `iam` operation from end to end.

## Testing Decisions

### What makes a good test

- A good test exercises behaviour through a public seam and asserts what a caller observes: an HTTP status, a response body, a cookie, a raised error, or the state of the database. It never asserts how the code reaches that result.
- A test that breaks when a private helper is renamed or a module is reorganized tests the implementation, not the behaviour, and is rewritten.
- A test calls a service with fakes passed as arguments. Nothing uses `mock.patch`.

### Seams

The user confirmed four seams:

1. **The HTTP seam** is the primary seam. Tests use Django's test `Client` against the test database and cover the contract of every operation: status codes, bodies, cookies, problem types, JSON Pointers, CSRF, and the `404`, `405`, and `500` problems. `createsuperuser` is tested through `call_command` at this level.
2. **The service and selector seam**. Tests call services and selectors with value objects and with fakes for the ports, against the test database. They cover the business rules that the HTTP seam reaches only with heavy setup: "email in use", the concurrent registration that ends in `IntegrityError`, incorrect Credentials with a fake authenticator, ending a Session that does not exist, and the superuser flags.
3. **The value object seam**. Pure tests with no database cover each value object and the `StrValueObject` base: the `Email` normalization (spaces, NFKC, lowercase), the format check, the `DisplayName` and `RawPassword` limits, the password whitespace rule, and the code of each `InvalidValueError`.
4. **The architecture seam**. Tests in the architecture test package inspect every public function in services and selectors, check that no code calls `full_clean()` or its siblings, and check that no error code repeats across apps. import-linter and ruff enforce the rest.

The model field adapters and the middleware get no seam of their own. The HTTP seam covers them, because every registration writes and reads an `Email` through the field adapter and every error passes through the middleware.

### Prior art

- The existing HTTP tests for the `iam` views use `Client`, a JSON post helper, and status and body assertions. The new HTTP tests follow the same style against the new contract and replace the old tests.
- The existing tests for `get_env`, the parsers, and `str_enum_to_choices` move with that code into `rastro.common`.
- The existing middleware tests use `RequestFactory`. They are replaced by HTTP tests of the problem details format.
- Factories replace the `model_bakery` fixture in the root `conftest.py`.

## Out of Scope

- Spans, metrics, and decorators for services and selectors. They need their own observability plan.
- An `Idempotency-Key` header and ids generated by the client. Commands rely on natural idempotency.
- Any endpoint that reads a resource by id, and any id in a response.
- django-modern-rest. ADR 0001 records the plan to revisit it after its 1.0 release.
- Keycloak or any OpenID Connect provider. Moving to one changes the authentication flow and needs its own ADR.
- Celery, management commands, file storage, email sending, and external API clients. `CODING_STANDARDS.md` already covers them as edges and dependencies, and the first feature that needs one adds it.
- Pagination, filtering, and other list helpers.
- Password strength rules beyond the minimum length, and rate limiting of Session starts.
- Internationalization. Error responses carry no text, and `USE_I18N` stays off.
- A CI pipeline. The check gate runs locally.
- Changes to the Grafana dashboards. They do not filter by route, so the new URLs do not affect them.

## Further Notes

- The grilling session settled every rule in `CODING_STANDARDS.md`, the terms in `GLOSSARY.md`, and ADR 0001. A ticket that finds a gap in a rule asks the user before it changes the rule, and updates `CODING_STANDARDS.md` in the same change.
- The HackSoft Django Styleguide is the reference for the parts that rastro keeps from it. rastro deviates from it on purpose in five areas:
  - validation lives in value objects at the edges instead of `full_clean()` and `clean()`;
  - dependencies are explicit `Protocol` arguments instead of patched imports;
  - APIs are function-based views without DRF;
  - schemas live in their own module;
  - errors use RFC 9457 instead of `{"message", "extra"}`.
- A worked example of business validation outside `iam` came up during design: a spreadsheet import of event guests, with CPF, passport, birth date window, and guest limit rules. It is not part of this rewrite. When that domain exists, its value objects, its row-level error format, and its all-or-nothing import decision start from that example.
