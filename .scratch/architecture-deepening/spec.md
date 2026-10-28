# Deepen the repositories, the Session cookie, CSRF, and the validation problems

Status: ready-for-agent

## Problem Statement

An architecture review of `auth` and `common` at commit `d01337c` found five places where a change in one module breaks another module without a failed test:

- A use case test passes with `FakeUserRepository`, and the same code fails on Postgres. The fake accepts a second User with an email in use, while `SqlUserRepository.add` raises `EmailInUseError`. The fake's `remove` raises `KeyError`, while the Sql adapter raises `LookupError`. The sample app's `FakeNoteRepository` stores the aggregate with no `model_copy()`, and the sample app is the reference for every pattern. No test runs the same behaviour against both adapters of a port.
- Three repository methods have no production caller: `SessionRepository.update`, `SessionRepository.get_by_id`, and `UserRepository.remove`. Each one costs a Sql body, a fake body, and tests.
- The Session lifetime is computed twice. `Session.start` sets `expires_at` from the setting, and the Session cookie module reads the setting again for `max_age`. A change to one computation makes the cookie and the Session expire at different times, and no test fails. A client that ends an expired Session gets `401`, the cookie stays in the browser, and the row stays in the database.
- CSRF lives in five modules. `CsrfToken` sits in the common domain, but only presentation code uses it. The CSRF route belongs to `auth`, so a second app can only reach it through `auth`.
- A new value object rule, for example `ge=1`, answers `request.invalid_type` with no warning. The `case _` fallback in the problems module hides every Pydantic error type that has no case, which breaks the standard "raise in place of a fallback value".

## Solution

Each repository port gets one behaviour suite that runs against the fake and the Sql adapter, so a fake that diverges fails a test. The ports lose the three methods that no use case calls. `session_start` returns the Session's expiry with its Session token, and the cookie takes its expiry from the Session. Ending an expired Session succeeds and clears the cookie and the row. One common presentation module owns all of CSRF, including its route, which moves to `/api/v1/csrf`. A Pydantic error type with no case raises, so the response is `500`, and every known type has its own case.

The JSON body of every route stays the same. Two HTTP changes are visible to a client:

- The CSRF route moves from `/api/v1/auth/csrf` to `/api/v1/csrf`.
- `POST /api/v1/auth/session/end` with the token of an expired Session answers `204` and clears the cookie, where it answered `401`.

## User Stories

### Developer of rastro

1. As a developer, I want each fake repository to pass the same behaviour suite as its Sql adapter, so that a use case test that passes with the fake also passes on Postgres.
2. As a developer, I want `FakeUserRepository.add` to raise `EmailInUseError` for an email in use, so that a use case test sees the same conflict as production.
3. As a developer, I want every fake `remove` and `update` to raise `LookupError` for a missing id, so that a missing aggregate fails the same way in a test and in production.
4. As a developer, I want `FakeNoteRepository` to store and return a `model_copy()`, so that the sample app teaches the copy rule that `CODING_STANDARDS.md` states.
5. As a developer, I want the behaviour suite to open the database only for the Sql adapter, so that the fake case runs without Postgres.
6. As a developer, I want a test that only makes sense on Postgres to stay a Sql-only test, so that the suite holds no test that the fake cannot pass.
7. As a developer, I want each behaviour to have one test, so that a change of behaviour edits one place.
8. As a developer, I want the repository ports to declare only the methods that a use case calls, so that a new adapter implements no dead method.
9. As a developer, I want `SessionRepository.update`, `SessionRepository.get_by_id`, and `UserRepository.remove` deleted with their bodies and tests, so that no code exists only to test itself.
10. As a developer, I want the coding standards to drop the list of Evans's method names, so that no reader takes the list as a set of required methods.
11. As a developer, I want `session_start` to return a `SessionStartOutput` with the Session token and `expires_at`, so that the presentation reads the expiry from the Session it started.
12. As a developer, I want the Session cookie module to stop reading `session_lifetime`, so that the Session lifetime has one computation, in `Session.start`.
13. As a developer, I want a view test that compares the cookie's expiry with the stored Session's `expires_at`, so that a drift between the two fails a test.
14. As a developer, I want all of CSRF in one common presentation module, so that I read and change CSRF in one file.
15. As a developer, I want `CsrfToken` out of the domain, so that the domain holds no presentation concern.
16. As a developer of a new app, I want the CSRF route to belong to `common`, so that my app uses CSRF without a dependency on `auth`.
17. As a developer, I want every router to keep `dependencies=[Depends(csrf_check)]`, so that a new app still cannot forget the check.
18. As a developer, I want a Pydantic error type with no case to raise, so that a new rule fails its view test before a deploy.
19. As a developer, I want each Pydantic type error that rastro's DTOs and value objects raise today to have its own case, so that today's responses stay the same.

### Client of the API

20. As a client, I want the Session cookie to expire at the Session's `expires_at`, so that the browser drops the cookie when the server stops accepting it.
21. As a client, I want `POST /api/v1/auth/session/start` to keep answering `204` with no body, so that the client code for sign-in does not change.
22. As a client, I want ending an expired Session to answer `204` and clear the cookie, so that a sign-out always leaves the browser with no Session cookie.
23. As a client, I want ending with no cookie, or with a token that no Session holds, to keep answering `401`, so that a request that never had a Session still fails.
24. As a client, I want `GET /api/v1/csrf` to set the CSRF cookie with the same name, flags, and token size as the old route, so that only the URL changes.
25. As a client, I want every validation problem body for today's input to stay the same, so that the frontend messages keep their types.

### Operator of rastro

26. As an operator, I want an expired Session that its client ends to leave the database, so that a sign-out deletes the row in every case.
27. As an operator, I want the Session and CSRF settings to keep their names and defaults, so that no deployment changes its environment.

## Implementation Decisions

The work splits into six tickets under `issues/`. Each ticket is one PR. Only ticket 2 waits for another ticket, ticket 1.

### 1. Delete the repository methods that no use case calls

- Delete `SessionRepository.update`, `SessionRepository.get_by_id`, and `UserRepository.remove` from the ports, from the Sql adapters, and from the fakes.
- `UserRepository.update`, `UserRepository.get_by_id`, and `SessionRepository.remove` stay, because use cases call them.
- In `CODING_STANDARDS.md`, delete the sentence "Its methods use Evans's names: ...", and add no sentence in its place. The existing rule that a port describes the business operation as it is today covers the case. The rules about `next_id`, `add`, `update`, `remove`, and `get_by_*` that follow the sentence stay, with their introduction reworded to stand without it.

### 2. One behaviour suite per repository port

- The suite covers `UserRepository`, `SessionRepository`, and the sample app's `NoteRepository`.
- A parametrized fixture returns the fake or the Sql adapter. A test reads back through the same port. For the Sql adapter, the read goes through a second database session, so the identity map hides nothing.
- The fakes change to pass the suite: `FakeUserRepository.add` raises `EmailInUseError` for an email in use, every fake `remove` raises `LookupError` with a message for a missing id, and `FakeNoteRepository` stores and returns a `model_copy()`.
- The behaviour tests leave the per-adapter test modules, so each behaviour has one test.
- These tests stay Sql-only: a row that breaks its value object (the bad email and the id `0`), the audit columns that the database sets, and the query span that keeps no parameters.

### 3. The Session cookie takes its expiry from the Session

- A new Output DTO, `SessionStartOutput`, holds the `SessionToken` and `expires_at`. `session_start` returns it in place of the bare `SessionToken`.
- The response of `session_start_view` stays `204` with no body. The view passes the Output to the Session cookie module.
- The Session cookie sets `Expires` to `expires_at` and sets no `Max-Age`. The presentation needs no clock. A wrong client clock changes how long the browser keeps the cookie, and the server still checks `Session.is_active` on each request.
- ADR 0002 is unaffected: `session_start` still writes the Session and the rehashed User in one transaction.

### 4. Ending an expired Session succeeds

- `session_end` deletes the Session that the token finds, whether or not the Session is active. With no token, or with a token that no Session holds, it raises `NotAuthenticatedError` as today. `session_get` keeps its rule: an expired Session is not authenticated.
- The view deletes the Session cookie after every `session_end` that succeeds.

### 5. One CSRF module in the common presentation

- One common presentation module holds `CsrfToken`, `SAFE_METHODS`, `csrf_check`, the CSRF cookie, and its own `APIRouter` with the route that sets the cookie. It follows the shape of the Session cookie module.
- `CsrfToken` keeps its `generate` and `matches` methods and its `SecretStr` root. It leaves the common domain.
- `CsrfFailedError` stays in the common presentation errors with its status row.
- The route moves from `/api/v1/auth/csrf` to `/api/v1/csrf`. The auth router loses `csrf_set_view`. `create_app` includes the common router.
- The six CSRF settings keep their names and defaults.
- The module that holds `csrf_check` and `csrf_cookie_set` today has no other member, so it goes away.

### 6. Every Pydantic error type has an explicit case

- The `case _` branch of the problems module raises a built-in exception whose message names the Pydantic error type. The handler chain answers `500`.
- Each Pydantic type error that rastro's DTOs and value objects raise today gets an explicit case that answers `request.invalid_type`, for example `int_type` for `"coats": "two"`. The implementer finds the list from the field types of every DTO and value object.
- No validation problem body changes for today's input.

## Testing Decisions

A good test exercises the module through its interface: the port for a repository, and HTTP for a view. It asserts behaviour that a caller sees, never a private function or an internal attribute. The tests follow the kinds in `CODING_STANDARDS.md`, use no `mock.patch`, and compare the literal JSON of each problem.

- **Ticket 1** adds no test. The repository tests of the three deleted methods go away, and a test that read through `SessionRepository.get_by_id` reads through `get_by_hashed_token`.
- **Ticket 2** tests at the repository port. Prior art: the repository tests of `auth` and the sample repository tests in `common`, which already read back through a second database session.
- **Ticket 3** tests at HTTP and at the use case. A view test compares the cookie's `Expires` with the `expires_at` of the stored row. A use case test asserts the fields of `SessionStartOutput`. Prior art: the view tests of `session_start` and the `other_session_cookie_settings` fixture.
- **Ticket 4** tests at HTTP. A view test ends an expired Session and asserts `204`, the cleared cookie, and a row count of `0`. This test replaces the test that today asserts `401` and a row count of `1`. Prior art: the view tests of `session_end`.
- **Ticket 5** tests at HTTP through the sample client. The tests that set the CSRF cookie move from `auth` to `common` and call `/api/v1/csrf`. A test asserts that `/api/v1/auth/csrf` answers `404`. Prior art: the CSRF tests in `common` and the CSRF view tests in `auth`.
- **Ticket 6** tests at HTTP through the sample client. One case sends a known type error and asserts `request.invalid_type`. One case triggers a Pydantic error type with no case and asserts the `500` problem. The sample app's paint route may need a new field to raise such a type. Prior art: the validation tests in `common`.

Each ticket runs the checks in `README.md` before it is done.

## Out of Scope

- A task that deletes the Sessions whose lifetime has run out with no client to end them. Its ticket is `.scratch/expired-session-cleanup/issues/01-delete-expired-sessions.md`.
- One registration call per app in `create_app`. The architecture test already finds an error class with no status row, so the gain is small, and the change touches ADR 0001.
- An architecture test that lists every Pydantic error type that the declared constraints can raise. The view tests that the standards require for each rejection find a missing case through the `500`.
- A change of the Session lifetime, the cookie names, or the cookie flags.
- A frontend change. The repository holds no frontend, and the move of the CSRF route assumes that no client uses `/api/v1/auth/csrf` today.

## Further Notes

- Ticket 1 comes before ticket 2, so the behaviour suite holds no test for a method that ticket 1 deletes.
- The review report that found these candidates was a temporary HTML file, so this spec is the only record of the findings.
- `GLOSSARY.md` and the ADRs need no change. A Session already ends "when the client ends it or when its lifetime runs out", and ending an expired Session fits that definition.
