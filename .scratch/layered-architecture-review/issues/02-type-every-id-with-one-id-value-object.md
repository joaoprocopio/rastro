# 02: Type every id with one `Id` value object

**What to build:** Every aggregate id in rastro is an `Id` value object that holds a positive integer, and a row with id `0` fails when it becomes an aggregate. Read the spec (`.scratch/layered-architecture-review/spec.md`, section Ids), `CODING_STANDARDS.md`, and the ADRs before you start, and follow the auto mode that the spec's Further Notes describe.

Add `Id` to the common domain's `value_objects` module. Type `User.id`, `Session.id`, `Session.user_id`, and the sample app's `Note.id` as `Id`, and convert in the infrastructure mappers. `next_id` receives the column object as `column` and returns an `Id`, and `existing_row` receives an `Id`. Update the fakes and their tests.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] A domain test shows that `Id` rejects `0`, `-1`, `"1"`, and `True`, and accepts `1`.
- [ ] A repository test against Postgres shows that `next_id` returns an `Id`, and that two calls return two different ids.
- [ ] A repository test shows that a row with id `0` fails when the repository returns it as an aggregate.
- [ ] `next_id` reads the table and the column from the column object that it receives, and no module holds the column name as text.
- [ ] Every HTTP test passes with an unchanged assertion.
- [ ] Every check in the README passes.

## Comments
