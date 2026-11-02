# Add Grafana Faro to the frontend

Status: needs-triage
Type: feature

## Problem

The Grafana dashboards in `docker/grafana/provisioning/dashboards/` show only what the API and the worker export. A page that loads slowly, a JavaScript error, or a failed `fetch` in the browser leaves no span or log, so a trace starts at the API and never at the user's click.

## Solution

The frontend loads the Grafana Faro Web SDK (`@grafana/faro-web-sdk`) and its tracing package (`@grafana/faro-web-tracing`). Faro reports Web Vitals, errors, console logs, and sessions, and the tracing package wraps `fetch` in OpenTelemetry JS spans. Each request to the API carries a `traceparent` header, so the API's server span joins the browser's trace.

Deliverables:

- A Faro setup in the frontend, with the service name, the version, and the environment that match the `RASTRO_SERVICE_*` and `RASTRO_DEPLOYMENT_*` values of the API.
- A path from the browser to ClickHouse through the collector in `docker/otel/config.yaml`.
- `traceparent` and `tracestate` in `cors_allow_headers` in `src/rastro/settings.py`, because the preflight rejects any header outside that list today.
- `propagateTraceHeaderCorsUrls` in the Faro tracing setup, limited to the API origin, so no third-party request carries the header.

## Out of scope

- Session replay.
- New Grafana dashboards beyond one panel that shows a browser span joined to an API span.

## Acceptance criteria

- [ ] Given a page that calls the API, when the page loads, then ClickHouse holds one trace with the browser span as the parent of the API's server span.
- [ ] Given a JavaScript error in the page, when it throws, then ClickHouse holds a log record with the error and the session ID.
- [ ] Given a request to an origin other than the API, when the page sends it, then the request has no `traceparent` header.

## Open questions

- The repo has no frontend today. Does the frontend live in this repo or in its own repo, and which one ships first?
- Faro sends its own payload format, not OTLP. Does the collector use the `faro` receiver from `opentelemetry-collector-contrib`, or does compose add Grafana Alloy with `faro.receiver` in front of the collector? The `faro` receiver is not confirmed in the `0.148.0` image.
- The browser reaches the collector over the public internet. Which origin and path expose the receiver, which CORS origins does it allow, and what limits its request rate?
- Does Faro sample sessions, for example 10% in `prod` and 100% in development, to keep the ClickHouse volume bounded?
