import uuid

from django.contrib.auth import get_user
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
from opentelemetry.semconv._incubating.attributes import deployment_attributes
from opentelemetry.semconv.attributes import service_attributes

from rastro import settings

_resource = Resource(
    attributes={
        service_attributes.SERVICE_NAME: settings.SERVICE_NAME,
        service_attributes.SERVICE_NAMESPACE: settings.SERVICE_NAMESPACE,
        service_attributes.SERVICE_INSTANCE_ID: str(uuid.uuid4()),
        deployment_attributes.DEPLOYMENT_ID: settings.DEPLOYMENT_ID,
        deployment_attributes.DEPLOYMENT_ENVIRONMENT: settings.DEPLOYMENT_ENVIRONMENT,
    }
)


def _setup_tracer() -> None:
    tracer_provider = TracerProvider(resource=_resource)

    tracer_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_GRPC_ENDPOINT,
        insecure=True,
    )
    tracer_processor = BatchSpanProcessor(tracer_exporter)
    tracer_provider.add_span_processor(tracer_processor)

    trace.set_tracer_provider(tracer_provider)


def _setup_metrics() -> None:
    metric_exporter = OTLPMetricExporter(
        endpoint=settings.OTEL_GRPC_ENDPOINT,
        insecure=True,
    )

    metric_readers = [PeriodicExportingMetricReader(metric_exporter)]
    meter_provider = MeterProvider(resource=_resource, metric_readers=metric_readers)

    metrics.set_meter_provider(meter_provider)


def _setup_logs() -> None:
    log_exporter = OTLPLogExporter(
        endpoint=settings.OTEL_GRPC_ENDPOINT,
        insecure=True,
    )
    log_processor = BatchLogRecordProcessor(log_exporter)
    logger_provider = LoggerProvider(resource=_resource)
    logger_provider.add_log_record_processor(log_processor)

    _logs.set_logger_provider(logger_provider)


def _instrument_django() -> None:
    def response_hook(
        span: trace.Span, request: HttpRequest, response: HttpResponse
    ) -> None:
        user = get_user(request)

        if (
            user is not None
            and hasattr(user, "is_authenticated")
            and user.is_authenticated
        ):
            span.set_attribute("user.id", str(user.pk))

            email: str | None = getattr(user, user.get_email_field_name())

            if email is not None:
                span.set_attribute("user.email", str(email))

    DjangoInstrumentor().instrument(response_hook=response_hook)


def _instrument_logging() -> None:
    LoggingInstrumentor().instrument()


def _instrument_psycopg2() -> None:
    Psycopg2Instrumentor().instrument(capture_parameters=True)


def instrument() -> None:
    _setup_tracer()
    _setup_metrics()
    _setup_logs()

    _instrument_logging()
    _instrument_psycopg2()
    _instrument_django()
