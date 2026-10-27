# 02: Type every id with one `Id` value object

**What to build:** Every aggregate id in rastro is an `Id` value object that holds a positive integer, and a row with id `0` fails when it becomes an aggregate. Read the spec (`.scratch/layered-architecture-review/spec.md`, section Ids), `CODING_STANDARDS.md`, and the ADRs before you start, and follow the auto mode that the spec's Further Notes describe.

Add `Id` to the common domain's `value_objects` module. Type `User.id`, `Session.id`, `Session.user_id`, and the sample app's `Note.id` as `Id`, and convert in the infrastructure mappers. `next_id` receives the column object as `column` and returns an `Id`, and `existing_row` receives an `Id`. Update the fakes and their tests.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] A domain test shows that `Id` rejects `0`, `-1`, `"1"`, and `True`, and accepts `1`.
- [x] A repository test against Postgres shows that `next_id` returns an `Id`, and that two calls return two different ids.
- [x] A repository test shows that a row with id `0` fails when the repository returns it as an aggregate.
- [x] `next_id` reads the table and the column from the column object that it receives, and no module holds the column name as text.
- [x] Every HTTP test passes with an unchanged assertion.
- [x] Every check in the README passes.

## Comments

### Decisions

- **Gap: where the test of a row with the id `0` lives.** The sample `NoteRepository` reads a Note only by id, and `get_by_id` takes an `Id`, so no call reaches a row with the id `0`. Chosen: `test_a_row_with_the_id_0_fails_to_become_a_user` in `rastro/auth/tests/repositories/test_user_repository.py` reads the row through `get_by_email`. Rejected: a new lookup on the sample port only for this test, and a `get_by_id(0)` call with a `type: ignore`.
- **Gap: the type of the `column` argument of `next_id`.** Chosen: `InstrumentedAttribute[int]`, the type of `UserRow.id` on the class. `next_id` narrows `column.expression` to a `Column`, raises `TypeError` for any other expression, and reads `table.fullname` and `name` from it. Rejected: `Mapped[int]`, which has no `expression`; `column.table`, which SQLAlchemy types as `Any`; and a `Column[int]` from `UserRow.__table__.c`, which looks the column up by a string key.
- **Gap: the type of the `id` argument of `get_by_id` on each port, repository, and fake.** The ticket names only `existing_row`. Chosen: every `get_by_id` takes an `Id`, and the dicts of the fakes use `Id` keys, so every id in the domain has one type. Rejected: `get_by_id(id: int)`, which would make each caller convert back to `int`.
- **Gap: "every HTTP test passes with an unchanged assertion".** `Id(1) == 1` is false, because a Pydantic `RootModel` equals only a `RootModel`. Two view tests compare an `int` from the database or from the span with the fixture's `user.id`. Chosen: `test_session_start.py` and `test_telemetry.py` compare with `user.id.root`. Every assertion on a status, a body, a header, or a cookie stays unchanged. Rejected: an `__eq__` on `Id` that accepts an `int`, which breaks the rule that a value object equals only its own class. `CODING_STANDARDS.md` now states the `.root` rule.
- **Gap: the `user.id` span attribute until ticket 05 removes it.** OpenTelemetry accepts only primitive attribute values. Chosen: `_trace_user` writes `session.user_id.root`. Rejected: removing the helper here, which is the scope of ticket 05.
