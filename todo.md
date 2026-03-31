# todo otel

0.  fazer teste de carga pelo k6

1.  Service Health Overview (Executive View)

- Request rate (RPS)
- Error rate (4xx/5xx)
- p50/p95/p99 latency
- Active users count
- Service uptime/availability status

2. HTTP/API Performance

- Latency percentiles (p50, p95, p99) by endpoint
- Throughput per endpoint (top 10)
- Slowest endpoints
- Response size distribution

3. User Activity

- Requests per user (top active users)
- Authenticated vs anonymous traffic ratio
- User error rates
- Request patterns by user email

4. Errors & Exceptions

- Error rate timeline
- Top error types/endpoints
- Recent logs with ERROR level
- Stack trace drill-down (linked to traces)

5. Logs Explorer

- Log volume over time
- Logs by severity level
- Filter by deployment_environment, service_name
- Correlate logs to traces

# ddd

- [ ] entrar mais a fundo nos conceitos de shared kernel, anti-corruption layer, conformist, aggregate, domain event, specification pattern
