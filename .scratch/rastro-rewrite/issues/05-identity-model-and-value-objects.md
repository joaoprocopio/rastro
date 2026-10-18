# 05: The Identity model and the iam value objects

**What to build:** Replace `IdentityModel` with the `Identity` model and give `iam` its value objects, so that an Identity has one representation and each validation rule has one implementation. The existing endpoints keep working: the old DDD code is adapted to the new model in this ticket and deleted by later tickets. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The value objects follow the spec's "Value objects in iam" section: `Email` (spaces stripped, Unicode NFKC, whole address lowercased, rastro's own format check), `DisplayName` (spaces stripped, at most 320 characters), `RawPassword` (spaces kept, at least 8 characters), and `HashedPassword`. The values module imports nothing outside the standard library and the value object module of `rastro.common`.

The model follows the spec's "The Identity model" section. Its email and display name use field adapters that convert to and from the value objects, raise when the database returns an invalid value, and turn `InvalidValueError` into Django's `ValidationError` for the admin. The existing migrations are deleted and replaced with a new initial migration.

**Blocked by:** 03 (Building blocks in rastro.common)

**Status:** ready-for-agent

- [x] Pure tests cover each value object: `" Ana@X.com "` becomes `ana@x.com`, a full-width address becomes its plain form, an invalid address fails with `iam.invalid_email`, a 321-character name fails with `iam.invalid_display_name`, a 7-character password fails with `iam.invalid_password`, and a password with spaces keeps them.
- [x] The model is `Identity` with the table `iam_identity`, it has `created_at` and `updated_at`, and it has no `date_joined`.
- [x] Reading an Identity from the database gives `Email` and `DisplayName` value objects, and a lookup by a raw email string finds the normalized address.
- [x] The database refuses an email that has uppercase letters, and refuses a second Identity with the same email.
- [x] `REQUIRED_FIELDS` includes `display_name`.
- [x] The Django admin rejects an invalid email and shows the error on the field.
- [x] One new initial migration replaces the old migrations.
- [x] The existing registration, Session, and CSRF endpoints still pass their HTTP tests on the new model.
- [x] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.

## Comments

Verified on branch `ticket-05`, before the merge of `rastro-rewrite`:

- `src/rastro/iam/tests/test_values.py` holds the pure tests: `" Ana@X.com "` becomes `ana@x.com`, `ａｎａ＠ｘ.ｃｏｍ` becomes `ana@x.com`, six invalid addresses fail with `iam.invalid_email`, 321 characters fail with `iam.invalid_display_name`, 7 characters fail with `iam.invalid_password`, and `"  pass word  "` keeps its spaces.
- `src/rastro/iam/tests/test_models.py` checks the table `iam_identity`, `created_at` and `updated_at` without `date_joined`, `REQUIRED_FIELDS`, the value objects on read, the lookup by `" Ana@X.com "`, the `IntegrityError` for an uppercase email written with raw SQL and for a duplicate email, and the `InvalidValueError` for an invalid email that the database returns.
- `src/rastro/iam/tests/test_admin.py` posts to `/admin/iam/identity/add/`: an invalid email shows `iam.invalid_email` on the `email` field, and `" Ana@X.com "` is stored as `ana@x.com`. This proves that the adapters survive `full_clean()` and the `MaxLengthValidator`.
- The old DTO base stripped every string, so a registration lost the spaces of a password. `DTO` no longer strips, and `test_views.py` registers with `"  pass word  "` and gets `401` for `"pass word"`.
- One migration, `0001_initial.py`, replaces the old one, and `makemigrations --check` reports no change.
- The gate: `ruff check`, `ruff format --check`, `mypy`, and `pytest` (90 passed) are green. `docker compose build django` builds the image. I did not run `docker compose up --build`, because the ports belong to the main directory; the merger runs the full stack.
- Open for later tickets: the manager keeps the old `UserManager` copy (ticket 07), and the `StrValueObjectField` base lives in `rastro/iam/fields.py` until a second app needs it.
