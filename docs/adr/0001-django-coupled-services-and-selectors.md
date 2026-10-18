---
status: accepted
---

# Couple the core to Django, with services, selectors, edge value objects, and explicit dependencies

rastro first kept its domain independent of Django, with DDD layers (`domain/`, `application/`, `infrastructure/`, `presentation/`), aggregates, repository ports, and mappers. One login request changed the shape of its data about 8 times, from the ORM model to the aggregate, the output DTO, the public DTO, and JSON, and the same field list was written about 5 times. We decided to couple the core to the Django ORM and to follow the HackSoft Django Styleguide: business logic lives in services, which write, and selectors, which read, and the Django model is the only representation of an Identity. Three ideas from the old design stay, because they are what made it worth having: validation in value objects, dependencies that a service declares in its signature, and the domain language in `GLOSSARY.md`.

## Considered options

- **Keep the DDD layers.** This keeps the domain testable without a database, but every change pays for the mappers, and the copies of the model drifted apart. For example, three different rules normalized the email address.
- **Fat models (Active Record).** This removes the mappers, but the model becomes the place where every rule lands, and a rule that spans models has no clear home.
- **django-modern-rest in place of plain Django views.** It removes the request parsing code and generates OpenAPI, but it is in Alpha, breaks its API in most releases, and exempts every controller from CSRF by default. We revisit it after its 1.0 release.

## Consequences

- Validation happens once, at the edges: the API, the model fields that read from the database, the manager that `createsuperuser` calls, and clients of external services. Services and selectors accept only value objects. A value object is a frozen dataclass whose module imports no framework, and one adapter per framework connects it to Pydantic and to the ORM.
- A service receives every dependency as a required keyword-only argument typed with a `Protocol`, and no dependency argument has a default. Each edge passes the real implementations from the app's `deps.py`. We chose required arguments over defaults so that mypy finds every caller that a new dependency affects, at the cost of more edits as the project grows.
- Service and selector tests use the test database, because the core now depends on the ORM.
- import-linter contracts, ruff rules, and pytest architecture tests check these rules, as `CODING_STANDARDS.md` describes.
