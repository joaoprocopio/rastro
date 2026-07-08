# rastro

projeto experimental para testar a instrumentação do django com opentelemetry.
project to experiment setting up the complete grafana stack + opentelemetry with django.

## checking

```sh
uv run ruff check src/ # linting
uv run mypy src/ # static type-checking
uv run pytest # testing
uv run python manage.py check # django check
```
