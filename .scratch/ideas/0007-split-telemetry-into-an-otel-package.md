# Split telemetry into an otel package

Status: needs-triage
Type: refactor

## Problem

`src/rastro/telemetry.py` passes every exporter option in code: `endpoint=settings.otel_grpc_endpoint` and `insecure=True`, three times, and builds the `Resource` from `Settings` fields. An operator who wants to change the endpoint, the compression, or the batch sizes edits code, because the standard `OTEL_*` variables lose to the arguments. The file also mixes four jobs in one module: defaults, providers, instrumentors, and the entry point.

## Solution

Replace `telemetry.py` with a package `src/rastro/otel/` of four modules. The SDK reads its configuration from the standard `OTEL_*` variables, and rastro only sets defaults for the variables the environment leaves unset.

```text
src/rastro/otel/
  __init__.py       instrument(): applies defaults, sets up providers, instruments libraries
  defaults.py       defaults() -> dict of OTEL_* names to values; apply() calls os.environ.setdefault
  providers.py      create_resource(); _setup_tracer, _setup_metrics, _setup_logs; setup(resource)
  instrumentors.py  _INSTRUMENTORS table of (instrumentor class, options); hooks; instrument_all, uninstrument_all
```

### `__init__.py`

`instrument()` calls `defaults.apply()` first, and imports `providers` and `instrumentors` after it, because some instrumentations read their variables at import. It returns early with one log line when the exporter has no endpoint or auth to reach, in place of an export that fails on every batch.

```python
def instrument(service_name: str) -> None:
    defaults.apply(service_name)
    if not os.environ.get(OTEL_EXPORTER_OTLP_ENDPOINT):
        logger.info("OpenTelemetry is disabled")
        return
    from rastro.otel import instrumentors, providers
    providers.setup(providers.create_resource())
    instrumentors.instrument_all()
```

### `defaults.py`

Each key is a constant from `opentelemetry.sdk.environment_variables` or from the instrumentation package, never a bare string, unless the package exports no constant. Candidate defaults:

- `OTEL_SERVICE_NAME`: the service name.
- `OTEL_RESOURCE_ATTRIBUTES`: `service.namespace`, `deployment.id`, and `deployment.environment`, joined as `key=value` pairs with each value URL-quoted, because the SDK splits on `,` and `=`.
- `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=DELTA`, so a metric export carries only the series that changed in the interval.
- `OTEL_EXPORTER_OTLP_COMPRESSION=gzip`.
- `OTEL_PYTHON_LOG_HANDLER_LEVEL=INFO`, so DEBUG logs stay on the console.
- `OTEL_BLRP_MAX_QUEUE_SIZE`, `OTEL_BLRP_MAX_EXPORT_BATCH_SIZE`, and `OTEL_BLRP_SCHEDULE_DELAY` for the log batch processor.
- `OTEL_SEMCONV_STABILITY_OPT_IN=http,database`, so the HTTP and database spans use the stable attribute names.

`apply()` calls `os.environ.setdefault` for each pair, so a variable from the environment always wins.

### `providers.py`

The exporters take no arguments and read `OTEL_EXPORTER_OTLP_*` themselves. `create_resource()` returns `OTELResourceDetector().detect()`, which reads `OTEL_SERVICE_NAME` and `OTEL_RESOURCE_ATTRIBUTES`. Each `_setup_*` function builds one provider with its batch processor or periodic reader, sets it as the global provider, and returns it.

### `instrumentors.py`

One table holds every instrumentor with its options, so `instrument_all()` and `uninstrument_all()` loop over the same list, and a test can undo the instrumentation:

```python
_INSTRUMENTORS: tuple[tuple[type[BaseInstrumentor], dict[str, Any]], ...] = (
    (LoggingInstrumentor, {}),
    (SQLAlchemyInstrumentor, {...}),
)
```

Request and response hooks live in this module, next to the table. A hook that sets `user.id` on the server span belongs here, because the Grafana dashboards in `docker/grafana/provisioning/dashboards/` filter on `SpanAttributes['user.id']`.

## Out of scope

- New instrumentors or new span attributes, beyond what `telemetry.py` exports today.
- Changes to the Grafana dashboards.

## Acceptance criteria

- [ ] `src/rastro/telemetry.py` is gone, and `main.py` and `worker.py` call `rastro.otel`.
- [ ] Every exporter option comes from an `OTEL_*` variable, and an `OTEL_*` variable from the environment overrides each default in `defaults.py`.
- [ ] The tests in `src/rastro/auth/tests/views/test_telemetry.py`, `src/rastro/common/tests/test_tasks.py`, and `src/rastro/auth/tests/repositories/test_sql_user_repository.py` pass.

## Open questions

- `instrument_app`, `instrument_engine`, and `instrument_broker` take an object, so they do not fit a table of `instrument(**options)` calls. Do they stay as functions in `instrumentors.py`, or does `instrument()` take the app, the engine, and the broker?
- `OTELResourceDetector` sets no `service.instance.id`, and `telemetry.py` sets a `uuid4` today. Do two workers with DELTA temporality merge their points into one series without it?
- Do the `RASTRO_*` settings `service_name`, `service_namespace`, `deployment_id`, `deployment_environment`, and `otel_grpc_endpoint` stay in `Settings` as the source of the defaults, or does `.env.example` set the `OTEL_*` variables directly?
- The exporters use gRPC today. Does the package keep gRPC, or move to OTLP over HTTP?
