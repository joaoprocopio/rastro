import uuid

from django.http import HttpRequest, HttpResponse
from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv._incubating.attributes import (
    deployment_attributes,
    enduser_attributes,
)
from opentelemetry.semconv.attributes import service_attributes

from rastro.settings import telemetry as telemetry_settings

_resource = Resource(
    attributes={
        service_attributes.SERVICE_NAME: telemetry_settings.SERVICE_NAME,
        service_attributes.SERVICE_NAMESPACE: telemetry_settings.SERVICE_NAMESPACE,
        service_attributes.SERVICE_INSTANCE_ID: str(uuid.uuid4()),
        deployment_attributes.DEPLOYMENT_ID: telemetry_settings.DEPLOYMENT_ID,
        deployment_attributes.DEPLOYMENT_ENVIRONMENT: telemetry_settings.DEPLOYMENT_ENVIRONMENT,
    }
)

_instrumented = False


def _setup_tracer() -> TracerProvider:
    tracer_provider = TracerProvider(resource=_resource)

    tracer_exporter = OTLPSpanExporter(
        endpoint=telemetry_settings.OTEL_GRPC_ENDPOINT,
        insecure=True,
    )
    tracer_processor = BatchSpanProcessor(tracer_exporter)
    tracer_provider.add_span_processor(tracer_processor)

    trace.set_tracer_provider(tracer_provider)

    return tracer_provider


def _setup_metrics() -> None:
    metric_exporter = OTLPMetricExporter(
        endpoint=telemetry_settings.OTEL_GRPC_ENDPOINT,
        insecure=True,
    )

    metric_readers = [PeriodicExportingMetricReader(metric_exporter)]
    meter_provider = MeterProvider(resource=_resource, metric_readers=metric_readers)

    metrics.set_meter_provider(meter_provider)


def _setup_logs() -> None:
    log_exporter = OTLPLogExporter(
        endpoint=telemetry_settings.OTEL_GRPC_ENDPOINT,
        insecure=True,
    )
    log_processor = BatchLogRecordProcessor(log_exporter)
    logger_provider = LoggerProvider(resource=_resource)
    logger_provider.add_log_record_processor(log_processor)

    _logs.set_logger_provider(logger_provider)


def _record_identity(
    span: trace.Span, request: HttpRequest, response: HttpResponse
) -> None:
    # The span carries the Identity's id and never its email, so no personal data reaches ClickHouse.
    user = getattr(request, "user", None)

    if user is not None and user.is_authenticated:
        span.set_attribute(enduser_attributes.ENDUSER_ID, str(user.pk))


def instrument_django(*, tracer_provider: TracerProvider) -> None:
    DjangoInstrumentor().instrument(
        tracer_provider=tracer_provider,
        response_hook=_record_identity,
    )


def _instrument_logging() -> None:
    LoggingInstrumentor().instrument()


def _instrument_psycopg2() -> None:
    # SQL parameters include password hashes, so the spans keep only the statement.
    Psycopg2Instrumentor().instrument(capture_parameters=False)


def instrument() -> None:
    # manage.py runserver imports rastro.wsgi, so one process can reach here twice.
    global _instrumented

    if _instrumented:
        return

    _instrumented = True

    tracer_provider = _setup_tracer()
    _setup_metrics()
    _setup_logs()

    _instrument_logging()
    _instrument_psycopg2()
    instrument_django(tracer_provider=tracer_provider)
