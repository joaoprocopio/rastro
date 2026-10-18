---
status: accepted
---

# Couple the core to Django and Pydantic, with services, selectors, and one error translation layer

rastro first kept its domain independent of Django, with DDD layers (`domain/`, `application/`, `infrastructure/`, `presentation/`), aggregates, repository ports, and mappers. One login request changed the shape of its data about 8 times, and the same field list was written about 5 times. We decided to couple the core to the Django ORM and to Pydantic, and to follow the HackSoft Django Styleguide: business logic lives in services, which write, and selectors, which read, and the Django model is the only representation of an Identity. Validation lives in value objects that are frozen Pydantic models, every dependency is a required `Protocol` argument, every error is a class that carries its own code and HTTP status, and one module translates every foreign error into a rastro error and every rastro error into an RFC 9457 response.

## Considered options

- **Keep the DDD layers.** This keeps the domain testable without a database, but every change pays for the mappers, and the copies of the model drifted apart. For example, three different rules normalized the email address.
- **Fat models (Active Record).** This removes the mappers, but the model becomes the place where every rule lands, and a rule that spans models has no clear home.
- **Framework-free value objects.** The first rewrite used frozen dataclasses that imported nothing. Pydantic still parsed them at the edge, so rastro needed a hand-written `__get_pydantic_core_schema__`, a parse helper at every edge, an `InvalidValueError` to carry a code, and imperative `__post_init__` rules in place of `StringConstraints`. Pydantic does all of this when the value object is a `RootModel`.
- **Errors without an HTTP status, and a status table in the middleware.** This kept HTTP out of the errors, because a service also runs in a Celery task. The table repeated every code as a string, and a new error needed an edit in two places. A Celery task ignores the status, so the status on the error costs nothing there.
- **Codes derived from the app label and the class name.** This makes every code unique by construction, but a class rename changes the HTTP contract with no warning. The base error class rejects a repeated code at import time in its place.
- **Pydantic errors per value object (`iam.invalid_email`).** This needs a wrap validator on every value object to replace Pydantic's error with a rastro one. Codes for the rule that failed (`request.too_short`) need no validator and tell the frontend more.
- **Identity without `AbstractBaseUser`.** This removes `set_password` from the model, but Django's `ModelBackend` calls `set_password` to equalize timing for an unknown email, so rastro would own the authentication backend, the hash upgrade, and the Session hash.
- **django-modern-rest in place of plain Django views.** It removes the request parsing code and generates OpenAPI, but it is in Alpha, breaks its API in most releases, and exempts every controller from CSRF by default. We revisit it after its 1.0 release.
- **SQLModel, or schemas generated from models.** One class for the table and the schema removes a declaration, but SQLModel replaces the Django ORM, the admin, and `contrib.auth`, and a generated schema changes the HTTP contract whenever the model changes. Output schemas read the model with `from_attributes` in their place.

## Consequences

- Validation happens once, at the edges: the views, the model and form fields, the manager that `createsuperuser` calls, and clients of external services. Services and selectors accept only value objects and import no Pydantic.
- The problems module is the only place that knows Pydantic's error types or builds a problem body, and a pytest architecture test checks this.
- A service receives every dependency as a required keyword-only argument typed with a `Protocol`, and no dependency argument has a default, so mypy finds every caller that a new dependency affects.
- Service and selector tests use the test database, because the core depends on the ORM.
- import-linter contracts, ruff rules, and pytest architecture tests check these rules, as `CODING_STANDARDS.md` describes.
