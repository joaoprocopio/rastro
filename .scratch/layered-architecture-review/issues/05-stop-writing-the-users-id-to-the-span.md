# 05: Stop writing the User's id to the span

**What to build:** The Session repository stops setting the User's id on the current span, and the request, query, and task spans stay. Read the spec (`.scratch/layered-architecture-review/spec.md`, section Telemetry), `CODING_STANDARDS.md`, the ADRs, and the Decisions of ticket 02 before you start, and follow the auto mode that the spec's Further Notes describe.

Remove the helpers of the Session repository that write `user.id`, and the test that asserts the attribute. In `CODING_STANDARDS.md`, drop the paragraph that describes the attribute, and keep the rule that a span never holds personal data.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] A signed-in request to `GET /api/v1/auth/session` still produces its request span and its query spans, and no span holds the User's email.
- [ ] The Session repository imports no OpenTelemetry module.
- [ ] `CODING_STANDARDS.md` describes no `user.id` attribute and keeps the rule against personal data in a span.
- [ ] Every check in the README passes.

## Comments
