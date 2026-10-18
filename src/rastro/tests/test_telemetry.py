from collections.abc import Iterator

import pytest
from django.test import Client
from django.urls import reverse
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind

from rastro import telemetry
from rastro.iam.tests.factories import IdentityFactory


@pytest.fixture
def exporter() -> Iterator[InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    telemetry.instrument_django(tracer_provider=tracer_provider)

    yield exporter

    DjangoInstrumentor().uninstrument()


def _request_span(exporter: InMemorySpanExporter) -> ReadableSpan:
    spans = [
        span for span in exporter.get_finished_spans() if span.kind == SpanKind.SERVER
    ]
    assert len(spans) == 1
    return spans[0]


def test_authenticated_request_records_the_identity_id_and_not_the_email(
    exporter: InMemorySpanExporter, client: Client, db: None
) -> None:
    identity = IdentityFactory.create()
    client.force_login(identity)

    client.get(reverse("iam:session_current"))

    attributes = dict(_request_span(exporter).attributes or {})
    assert attributes["enduser.id"] == str(identity.pk)
    assert identity.email.root not in attributes.values()


def test_anonymous_request_records_no_enduser_id(
    exporter: InMemorySpanExporter, client: Client, db: None
) -> None:
    client.get(reverse("iam:session_current"))

    attributes = dict(_request_span(exporter).attributes or {})
    assert "enduser.id" not in attributes
