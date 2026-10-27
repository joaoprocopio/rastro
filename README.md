# rastro

An experimental FastAPI project that defines the patterns other projects copy, built on SQLAlchemy 2 and taskiq in four layers, and instrumented with OpenTelemetry and Grafana. `CODING_STANDARDS.md` holds the patterns, and `docs/adr/0001-layers-with-fastapi-sqlalchemy-and-taskiq.md` records why rastro uses this stack.

## Run the stack

```shell
docker compose up --build
```

The `migrate` service runs the Alembic migrations. Then the API answers on `http://localhost:8000`, the `worker` service runs the tasks that the API sends, and Grafana answers on `http://localhost:7141`.

## Run the API locally

`.env.example` holds the local value of every setting, and every setting is required:

```shell
docker compose up -d --wait postgres
uv run --env-file .env.example alembic upgrade head
uv run --env-file .env.example fastapi dev
```

To run the tasks that the API sends, start the worker in a second shell:

```shell
uv run --env-file .env.example taskiq worker rastro.worker:broker -w 1
```

## Run the checks

Each test run creates its own database on the Postgres server of `RASTRO_POSTGRES_URL` and drops it at the end, so parallel runs can share one server. If another rastro checkout already runs the `rastro` compose project, `docker compose up` reuses its Postgres container:

```shell
docker compose up -d --wait postgres
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run lint-imports
uv run pytest
```
