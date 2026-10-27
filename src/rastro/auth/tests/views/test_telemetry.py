import httpx
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind

from rastro.auth.domain.aggregates import User


def _request_attributes(spans: InMemorySpanExporter) -> dict[str, object]:
    (span,) = [s for s in spans.get_finished_spans() if s.kind == SpanKind.SERVER]
    assert span.attributes is not None
    return dict(span.attributes)


async def test_a_signed_in_request_span_carries_the_user_id_and_not_the_email(
    signed_in_client: httpx.AsyncClient, user: User, spans: InMemorySpanExporter
) -> None:
    await signed_in_client.get("/api/v1/auth/session")

    attributes = _request_attributes(spans)
    assert attributes["user.id"] == user.id
    assert "ana@example.com" not in str(attributes)


async def test_a_session_start_span_carries_the_user_id_and_not_the_email(
    client: httpx.AsyncClient, user: User, spans: InMemorySpanExporter
) -> None:
    await client.post(
        "/api/v1/auth/session/start",
        json={"email": "ana@example.com", "password": "password"},
    )

    attributes = _request_attributes(spans)
    assert attributes["user.id"] == user.id
    assert "ana@example.com" not in str(attributes)


async def test_a_session_end_span_carries_the_user_id(
    signed_in_client: httpx.AsyncClient, user: User, spans: InMemorySpanExporter
) -> None:
    await signed_in_client.post("/api/v1/auth/session/end")

    assert _request_attributes(spans)["user.id"] == user.id


async def test_a_request_without_a_session_carries_no_user_id(
    client: httpx.AsyncClient, spans: InMemorySpanExporter
) -> None:
    await client.get("/api/v1/auth/session")

    assert "user.id" not in _request_attributes(spans)


async def test_no_span_of_a_signed_in_request_holds_the_email(
    signed_in_client: httpx.AsyncClient, spans: InMemorySpanExporter
) -> None:
    response = await signed_in_client.get("/api/v1/auth/session")

    assert response.json()["email"] == "ana@example.com"
    attributes = [dict(span.attributes or {}) for span in spans.get_finished_spans()]
    assert "ana@example.com" not in str(attributes)
