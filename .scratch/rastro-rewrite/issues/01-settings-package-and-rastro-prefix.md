# 01: Settings package and the RASTRO_ prefix

**What to build:** Split the single settings module into a settings package and rename every environment variable to the `RASTRO_` prefix, so that each setting has one obvious home and a missing variable can never run production in debug mode. The app behaves the same for a person who uses it. Read the spec (`.scratch/rastro-rewrite/PRD.md`), `CODING_STANDARDS.md`, `GLOSSARY.md`, and ADR 0001 before you start.

The package has a base module with every setting, a test module that overrides values for the test run (including a fast password hasher), a telemetry module, and a sessions module. No setting exists only in production. Environment variables, read with `get_env`, switch features on and off.

This ticket also prepares the tooling that later tickets rely on: ruff bans `django.dispatch.receiver` and `csrf_exempt` through `TID251`, and factory_boy is a dev dependency.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Settings live in a package with base, test, telemetry, and sessions modules, and each setting is defined once.
- [ ] Every environment variable uses the `RASTRO_` prefix in place of `RASTRO_DJANGO_`, in the settings, `compose.yaml`, and the tests.
- [ ] `DEBUG` defaults to off. Without `DEBUG`, a missing `SECRET_KEY` stops the app at startup, and `SECRET_KEY` has no insecure default.
- [ ] `CSRF_COOKIE_HTTPONLY` is `False` and appears once.
- [ ] The unused `OTEL_HTTP_ENDPOINT` setting is gone.
- [ ] pytest runs with the test settings module, and the type checker uses the base module.
- [ ] ruff fails on an import of `django.dispatch.receiver` or `csrf_exempt`.
- [ ] factory_boy is installed as a dev dependency.
- [ ] Every existing HTTP test still passes without a change to its assertions.
- [ ] The check gate passes: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- [ ] `docker compose up --build` starts the stack and Django serves requests.
