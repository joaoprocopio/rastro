# 05: The Identity model and the iam value objects

**What to build:** Replace `IdentityModel` with the `Identity` model and give `iam` its value objects, so that an Identity has one representation and each validation rule has one implementation. The existing endpoints keep working: the old DDD code is adapted to the new model in this ticket and deleted by later tickets. Read the spec (`.scratch/rastro-rewrite/spec.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The value objects follow the spec's "Value objects in iam" section: `Email` (spaces stripped, Unicode NFKC, whole address lowercased, rastro's own format check), `DisplayName` (spaces stripped, at most 320 characters), `RawPassword` (spaces kept, at least 8 characters), and `HashedPassword`. The values module imports nothing outside the standard library and the value object module of `rastro.common`.

The model follows the spec's "The Identity model" section. Its email and display name use field adapters that convert to and from the value objects, raise when the database returns an invalid value, and turn `InvalidValueError` into Django's `ValidationError` for the admin. The existing migrations are deleted and replaced with a new initial migration.

**Blocked by:** 03 (Building blocks in rastro.common)

**Status:** ready-for-agent

- [ ] Pure tests cover each value object: `" Ana@X.com "` becomes `ana@x.com`, a full-width address becomes its plain form, an invalid address fails with `iam.invalid_email`, a 321-character name fails with `iam.invalid_display_name`, a 7-character password fails with `iam.invalid_password`, and a password with spaces keeps them.
- [ ] The model is `Identity` with the table `iam_identity`, it has `created_at` and `updated_at`, and it has no `date_joined`.
- [ ] Reading an Identity from the database gives `Email` and `DisplayName` value objects, and a lookup by a raw email string finds the normalized address.
- [ ] The database refuses an email that has uppercase letters, and refuses a second Identity with the same email.
- [ ] `REQUIRED_FIELDS` includes `display_name`.
- [ ] The Django admin rejects an invalid email and shows the error on the field.
- [ ] One new initial migration replaces the old migrations.
- [ ] The existing registration, Session, and CSRF endpoints still pass their HTTP tests on the new model.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
