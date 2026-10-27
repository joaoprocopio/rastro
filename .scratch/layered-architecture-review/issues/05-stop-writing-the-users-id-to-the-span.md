# 05: Stop writing the User's id to the span

**What to build:** The Session repository stops setting the User's id on the current span, and the request, query, and task spans stay. Read the spec (`.scratch/layered-architecture-review/spec.md`, section Telemetry), `CODING_STANDARDS.md`, the ADRs, and the Decisions of ticket 02 before you start, and follow the auto mode that the spec's Further Notes describe.

Remove the helpers of the Session repository that write `user.id`, and the test that asserts the attribute. In `CODING_STANDARDS.md`, drop the paragraph that describes the attribute, and keep the rule that a span never holds personal data.

**Blocked by:** 02

**Status:** resolved

- [x] A signed-in request to `GET /api/v1/auth/session` still produces its request span and its query spans, and no span holds the User's email.
- [x] The Session repository imports no OpenTelemetry module.
- [x] `CODING_STANDARDS.md` describes no `user.id` attribute and keeps the rule against personal data in a span.
- [x] Every check in the README passes.

## Comments

### Decisions

- **Gap: which tests asserted the `user.id` attribute.** Two places did: four tests in `rastro/auth/tests/views/test_telemetry.py` and `test_add_read_and_remove_set_the_user_id_on_the_current_span` in `rastro/auth/tests/repositories/test_session_repository.py`. Chosen: remove all five. Rejected: keeping the view tests with only their email assertion, because `test_no_span_of_a_signed_in_request_holds_the_email` already checks every span of a signed-in request.
- **Gap: how a test proves that the request and query spans stay.** No test checked that a span exists. Chosen: `test_a_signed_in_request_produces_its_request_span_and_its_query_spans` sends `GET /api/v1/auth/session` and asserts one `SERVER` span and at least one `CLIENT` span. Rejected: asserting span names, which change with the version of each instrumentation.
- **Gap: whether a test pins the absence of `user.id`.** The red step used a test that no span of a signed-in request has `user.id`. Chosen: delete that test after green, because the maintainer does not want the attribute now, and a test against it would block its return. Rejected: keeping the test as a guard.
- **Gap: the `.root` rule in `CODING_STANDARDS.md` names a span attribute.** No test compares an id with a span attribute now. Chosen: the rule names only a column. Rejected: leaving the span attribute in the rule.
