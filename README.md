# rastro

An experimental Django project that defines the patterns other Django projects copy, instrumented with OpenTelemetry and Grafana.

## Run the stack

```shell
docker compose up --build
```

The API answers on `http://localhost:8000`, and Grafana on `http://localhost:7141`.

## Run the checks

```shell
docker compose up -d postgres
uv sync
uv run ruff check src/
uv run ruff format --check src/
uv run mypy src/
uv run pytest
RASTRO_DEBUG=1 uv run python manage.py check
```
