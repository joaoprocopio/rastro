# 01: Create the Procrastinate schema with an Alembic migration

**What to build:** `alembic upgrade head` creates every table, function, and type of Procrastinate 3.10.0, beside the tables of rastro. The migration holds a frozen copy of the `schema.sql` that ships in Procrastinate 3.10.0 and runs it with `op.execute`, so an upgrade of the package changes no existing migration. The Alembic environment ignores every object whose name starts with `procrastinate_`, so `compare_metadata` against `Row.metadata` still reports no difference. `CODING_STANDARDS.md` describes how a later upgrade of Procrastinate adds its SQL: one Alembic migration for each file in the package's `sql/migrations/` between the two versions, with a `pre` file before the deploy of the new code and a `post` file after every worker runs it. The spec is `.scratch/delete-expired-sessions/spec.md`.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] After `alembic upgrade head`, the test database has the `procrastinate_jobs`, `procrastinate_periodic_defers`, `procrastinate_events`, and `procrastinate_workers` tables.
- [x] The migration test that compares the migrated database with `Row.metadata` reports no difference.
- [x] `alembic downgrade` of the migration removes every `procrastinate_` object.
- [x] `CODING_STANDARDS.md` holds the upgrade procedure for the Procrastinate schema.
- [x] Every check in the README passes.
