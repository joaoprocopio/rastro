# Spec: Rename the `account` context to `IAM` and redesign the authentication API

Status: ready-for-agent
Type: spec

## Problem Statement

The bounded context that owns "who you are and how you sign in" is currently called
`account`, with an `Account` aggregate and an `Account` Django model. Two problems have
accumulated:

- **The name no longer reflects the intent.** The maintainer wants this context to grow into
  full Identity & Access Management (authentication now, authorization later). `account` under-
  describes that ambition, and `Account` is a weak domain term for the authenticated subject.
- **The API and the internal vocabulary have drifted.** The endpoints use UI/transport verbs
  (`register`/`login`/`logout`), the application layer is named after those same UI verbs, and
  the Django auth model's framework vocabulary (`login`, `logout`, `logged_account`) has leaked
  into the domain ports. Names collide across layers and are papered over with import aliases.
- **A latent security decision was never made.** Sign-in reveals whether an email is registered
  (404 for unknown email vs 401 for wrong password), which is a user-enumeration oracle.

## Solution

Rename the context to **IAM** and re-express it in intention-revealing, layer-honest names,
with a resource-oriented HTTP API.

- The domain speaks of an **Identity** (the authenticated principal); the persistence layer keeps
  Django's **`IdentityModel`**; a mapper is the anti-corruption seam between them. Nothing is
  aliased — every type is named for exactly what it is.
- The API becomes **resource-oriented**: an `identities` collection and a `session` singleton,
  with HTTP methods carrying intent.
- The application layer is named for **domain intentions** (register an identity, authenticate,
  end a session, resolve the current identity), independent of both HTTP verbs and CRUD.
- **Sign-in becomes enumeration-resistant**: unknown email and wrong password return the same
  `401` with the same body.

Externally, an API client gets a cleaner, safer auth surface. Internally, the maintainer gets a
context whose names teach the architecture and that is ready to grow authorization concepts.

## User Stories

1. As an unauthenticated visitor, I want to create a new identity by submitting a display name,
   email, and password, so that I can obtain an account and be signed in immediately.
2. As a visitor signing up, I want a password of at least the minimum length to be required, so
   that weak credentials are rejected at the boundary.
3. As a visitor signing up, I want my password's leading/trailing whitespace preserved (never
   stripped), so that the password I chose is exactly the password I can later sign in with.
4. As a visitor signing up with an email that is already registered, I want a clear validation
   error, so that I understand the email is taken.
5. As a registered user, I want to sign in with my email and password, so that I get an
   authenticated session.
6. As a registered user, I want to be told only "incorrect email or password" when sign-in
   fails, so that the system is usable but does not reveal whether an email exists.
7. As a security-conscious user, I want an unknown email and a wrong password to produce an
   identical failure (same status, same body), so that my registration status cannot be probed.
8. As a registered user whose stored password hash is outdated, I want it transparently upgraded
   on a successful sign-in, so that my credentials stay on the current hashing scheme without any
   action from me.
9. As an authenticated user, I want to ask the API who I currently am, so that a client app can
   render my identity and session state.
10. As an unauthenticated caller, I want the "current identity" endpoint to tell me I am not
    authenticated, so that a client can route me to sign-in.
11. As an authenticated user, I want to sign out, so that my session is discarded.
12. As an API client, I want to obtain a CSRF token, so that I can make state-changing requests
    that satisfy Django's CSRF protection.
13. As an API client, I want the "current identity" response to expose only public fields
    (display name and email), so that no sensitive fields (password hash, permission flags) ever
    cross the wire.
14. As an API client, I want a malformed JSON request body to produce a structured `422`
    problem-detail response, so that I can handle validation errors uniformly.
15. As an API client, I want all errors returned as RFC 7807 `application/problem+json`, so that
    error handling is consistent across the API.
16. As an API client, I want authentication actions expressed as resources — create an identity,
    create/read/delete a session — so that the API reads predictably by HTTP method.
17. As the maintainer, I want the context named `IAM` (always uppercased in code identifiers), so
    that the naming signals its present and future scope.
18. As the maintainer, I want the domain aggregate called `IdentityAggregate` and the Django
    model called `IdentityModel`, so that the domain and persistence layers each speak their own
    honest language and never require import aliases.
19. As the maintainer, I want every type suffixed by its stereotype (`…Aggregate`, `…Model`,
    `…DTO`, `…Mapper`, `…UseCase`, `…Repository`, `…Service`, `…Error`), with value objects left
    as bare concept names, so that a name tells me which layer and role a type belongs to.
20. As the maintainer, I want the application use cases named for domain intentions
    (`RegisterIdentityUseCase`, `AuthenticateUseCase`, `EndSessionUseCase`,
    `GetCurrentIdentityUseCase`), so that they read the same regardless of transport.
21. As the maintainer, I want the `SessionService` domain port to speak session lifecycle
    (`start`, `end`, `current_identity`), with the Django adapter keeping framework words
    (`auth.login`/`auth.logout`/`auth.get_user`) trapped behind it, so that the domain stays free
    of framework vocabulary.
22. As the maintainer, I want the not-found error deleted once sign-in stops distinguishing, so
    that the error catalog carries no dead entries.
23. As the maintainer, I want the physical table named `iam_identity`, so that the database name
    is clean regardless of the model class name.
24. As the maintainer, I want the README and backlog references updated to the new vocabulary, so
    that documentation matches the code.
25. As an AFK agent picking this up, I want the full auth surface covered by HTTP-level tests, so
    that I can refactor confidently against externally observable behavior.

## Implementation Decisions

- **Context rename.** The `account` bounded context becomes `iam` (lowercase Python package and
  Django app label; the acronym `IAM` is uppercased wherever it appears as a word in an
  identifier, e.g. `IAMConfig`). `INSTALLED_APPS` and `AUTH_USER_MODEL` update accordingly;
  `AUTH_USER_MODEL` becomes `iam.IdentityModel`.

- **Naming convention (alias nothing; name each type for what it is).** Types carry a stereotype
  suffix: aggregates `…Aggregate`, Django models `…Model`, DTOs `…DTO`, mappers `…Mapper`, use
  cases `…UseCase`, repositories `…Repository`, services `…Service`, errors `…Error`. Value
  objects stay bare (`Email`, `DisplayName`, `RawPassword`, `HashedPassword`).

- **Domain aggregate vs Django model.** The domain aggregate is `IdentityAggregate`; the Django
  auth model is `IdentityModel`. They are distinct symbols imported side by side with no alias.
  The mappers form the anti-corruption boundary between them.

- **Persistence.** `IdentityModel` keeps the current `AbstractBaseUser` + `PermissionsMixin`
  shape and manager (renamed to `IdentityManager`), with `USERNAME_FIELD = "email"`.
  The initial migration is regenerated for the `iam` app.

- **Application layer.** Use cases: `RegisterIdentityUseCase`, `AuthenticateUseCase`,
  `EndSessionUseCase`, `GetCurrentIdentityUseCase`. DTOs (two-DTO output split retained):
  `RegisterIdentityInputDTO`, `AuthenticateInputDTO`, `IdentityOutputDTO` (internal, rich —
  **password field removed**), `IdentityPublicDTO` (client projection: display name + email).

- **Session port.** `SessionService` exposes `start(identity)`, `end()`, and
  `current_identity()`. `DjangoSessionService` implements them over Django's auth session,
  keeping `auth.*` vocabulary internal.

- **Authentication flow & enumeration resistance.** `AuthenticateUseCase` looks up by email; if
  the identity is absent **or** the password is incorrect, it raises a single
  `IncorrectCredentialsError` (HTTP 401) with an identical body in both cases. On success it
  upgrades the stored hash if needed, then starts a session. The previous not-found error and its
  code are deleted (no remaining callers).

- **Error catalog.** `ErrorCode` retains `BASE_VALIDATION_ERROR` and adds
  `IAM_INCORRECT_CREDENTIALS`; the two `AUTH_*` account codes are removed.

- **API contract (resource-oriented).**

  | Method | Path                     | Purpose                                | Success                       |
  | ------ | ------------------------ | -------------------------------------- | ----------------------------- |
  | POST   | `/api/v1/iam/identities` | Register a new identity (auto sign-in) | 201, `IdentityPublicDTO`      |
  | POST   | `/api/v1/iam/session`    | Authenticate (start a session)         | 200, `IdentityPublicDTO`      |
  | DELETE | `/api/v1/iam/session`    | End the current session                | 204                           |
  | GET    | `/api/v1/iam/session`    | Resolve the current identity           | 200 `IdentityPublicDTO` / 401 |
  | GET    | `/api/v1/iam/csrftoken`  | Issue a CSRF cookie                    | 200                           |

  `SessionView` dispatches its three methods to the three session-related use cases;
  `IdentitiesView` handles registration. No named routes / `reverse()` are added.

- **Error responses.** All errors continue to surface as RFC 7807
  `application/problem+json` through the existing exception-handling middleware; malformed
  request bodies yield `422` validation problem details.

## Testing Decisions

- **What makes a good test here.** Tests assert only externally observable behavior — HTTP status
  codes, response body shape/content, and session/cookie effects — never internal wiring (which
  factory built which use case, how the session is stored). A test should survive any refactor
  that preserves the API contract.

- **Primary seam — the HTTP boundary.** New integration tests drive the resource endpoints via
  Django's test `Client` against a real test database, one seam covering
  `urls → View → UseCase → Repository → IdentityModel → DB` for every flow: registration (201 +
  auto session), authentication success (200), authentication failure for both wrong password and
  unknown email returning an **identical** 401 body (enumeration resistance), session end (204),
  current-identity when authenticated (200) and when not (401), CSRF token issuance, and malformed
  JSON → 422.

- **Retained lower seam — mapper unit tests.** The existing mapper tests are kept and renamed to
  the `Identity*` vocabulary; they pin the `IdentityModel ↔ IdentityAggregate ↔ DTO` translations
  cheaply.

- **Modules under test.** The IAM presentation/views layer (via the HTTP seam) and the IAM
  mappers (via unit tests). Use cases, repository, and session service are exercised transitively
  through the HTTP seam rather than mocked in isolation.

- **Prior art.** `test_middleware.py` drives the request layer (via `RequestFactory`) and models
  the problem-detail assertions; `conftest.py` provides the database and identity fixtures;
  pytest-django supplies the `db` and `client` fixtures. The kept mapper tests are their own prior
  art for translation coverage.

## Out of Scope

- **Authorization.** Roles, permissions, and policies as first-class domain concepts are future
  work; only Django's inherited `PermissionsMixin` flags remain for now.
- **Profile / preferences.** `IdentityAggregate` stays strictly the authentication principal; no
  profile fields are added.
- **Token / non-session auth.** Only Django's session-cookie authentication is in scope.
- **The pre-existing `VALIDATION_ERROR` vs `BASE_VALIDATION_ERROR` test failures.** These predate
  this work and are left untouched.
- **Data migration.** The user-model app label changes, so the dev database is reset to a fresh
  volume rather than migrated in place (experimental project, no real data).

## Further Notes

- Because `AUTH_USER_MODEL` changes app label, the dev Postgres volume must be recreated before
  `migrate` — the same reset performed during the previous `conta → account` rename.
- This work intentionally exercises the "anti-corruption layer" and "conformist" concepts from the
  DDD backlog: `IdentityModel` (Django's framework model) is wrapped by mappers into the pure
  `IdentityAggregate`, and `DjangoSessionService` conforms to Django's auth session behind the
  domain `SessionService` port.
- Enumeration resistance closes one of the two decisions previously deferred in the error-handling
  design; the pydantic-ACL decision remains deferred and out of scope here.
