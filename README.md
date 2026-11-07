# rastro

An experimental FastAPI project that defines the patterns other projects copy, built on SQLAlchemy 2 and Procrastinate in four layers, and instrumented with OpenTelemetry and Grafana. `CODING_STANDARDS.md` holds the patterns, and `docs/adr/0001-layers-with-fastapi-sqlalchemy-and-procrastinate.md` records why rastro uses this stack.

## Run the stack

Every `docker compose` command on this page reads the published ports from `.env`, so copy `.env.example` first:

```shell
cp .env.example .env
docker compose up --build
```

The `migrate` service runs the Alembic migrations. Then the API answers on `http://localhost:8000`, the `worker` service runs the tasks, Grafana answers on `http://localhost:7141`, and Mailpit shows each email that rastro sends on `http://localhost:8025`.

## Run the API locally

`.env.example` holds the local value of every setting and every published port. Only `RASTRO_POSTGRES_URL` is required, and every other setting has a default. Without `OTEL_EXPORTER_OTLP_ENDPOINT`, the process exports no telemetry:

```shell
docker compose up -d --wait postgres
uv run --env-file .env.example alembic upgrade head
uv run --env-file .env.example fastapi dev
```

To run the tasks, start Mailpit and the worker in a second shell:

```shell
docker compose up -d mailpit
uv run --env-file .env.example procrastinate --app=rastro.worker.app worker
```

## Run the checks

Each test run creates its own database on the Postgres server of `RASTRO_POSTGRES_URL` and drops it at the end, so parallel runs can share one server. If another rastro checkout already runs the `rastro` compose project, `docker compose up` reuses its Postgres container. In a worktree with its own ports, run `uv run --env-file .env pytest`:

```shell
docker compose up -d --wait postgres
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run lint-imports
uv run pytest
```

## Run a second stack beside another worktree's

Each worktree under `worktrees/` can run its own stack, so two agents can run the API and the checks at the same time. To create a worktree from `main` with its own ports, run this command:

```shell
scripts/worktree.sh
```

The script names the worktree and its branch `wt-` and a random suffix, so give the branch its real name with `git branch -m`. It then runs `scripts/ports.sh`, which you run by hand in a worktree you created another way.

`scripts/ports.sh` takes nine random ports from 20000 to 32767 that no process listens on, and prints them. It writes the ports, the compose project name, `RASTRO_POSTGRES_URL`, `RASTRO_SMTP_PORT`, and `OTEL_EXPORTER_OTLP_ENDPOINT` into `.env`, and it keeps every other value. Run it again and it keeps the ports.

Every `docker compose` command on this page then works unchanged. The `uv run` commands that read the settings load `.env` in place of `.env.example`, because `.env.example` keeps the default ports:

```shell
uv run --env-file .env alembic upgrade head
uv run --env-file .env pytest
```

To remove the stack of a worktree with its volumes and the images it built, run this from the worktree root. It keeps the shared Postgres, ClickHouse, collector, and Grafana images:

```shell
docker compose down -v --rmi local
```

If `docker compose up` fails with `port is already allocated`, another stack holds a port, and `docker compose ls` shows which stack. Stop that stack, or draw new ports with `sed -i '/^COMPOSE_PROJECT_NAME=/d' .env && scripts/ports.sh`. `scripts/ports.sh` sees only the ports in use now, so a stopped stack can claim its ports back from a newer one.
