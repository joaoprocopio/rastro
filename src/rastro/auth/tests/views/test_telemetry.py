import httpx
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind


async def test_a_signed_in_request_produces_its_request_span_and_its_query_spans(
    signed_in_client: httpx.AsyncClient, spans: InMemorySpanExporter
) -> None:
    await signed_in_client.get("/api/v1/auth/session")

    kinds = [span.kind for span in spans.get_finished_spans()]
    assert kinds.count(SpanKind.SERVER) == 1
    assert SpanKind.CLIENT in kinds


async def test_no_span_of_a_signed_in_request_holds_the_email(
    signed_in_client: httpx.AsyncClient, spans: InMemorySpanExporter
) -> None:
    response = await signed_in_client.get("/api/v1/auth/session")

    assert response.json()["email"] == "ana@example.com"
    attributes = [dict(span.attributes or {}) for span in spans.get_finished_spans()]
    assert "ana@example.com" not in str(attributes)
