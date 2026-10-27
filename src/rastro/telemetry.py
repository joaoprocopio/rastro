import uuid

from fastapi import FastAPI
from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv._incubating.attributes import deployment_attributes
from opentelemetry.semconv.attributes import service_attributes
from sqlalchemy.ext.asyncio import AsyncEngine
from taskiq import AsyncBroker
from taskiq.middlewares.opentelemetry_middleware import OpenTelemetryMiddleware

from rastro.settings import Settings


def _resource(settings: Settings) -> Resource:
    return Resource(
        attributes={
            service_attributes.SERVICE_NAME: settings.service_name,
            service_attributes.SERVICE_NAMESPACE: settings.service_namespace,
            service_attributes.SERVICE_INSTANCE_ID: str(uuid.uuid4()),
            deployment_attributes.DEPLOYMENT_ID: settings.deployment_id,
            deployment_attributes.DEPLOYMENT_ENVIRONMENT: settings.deployment_environment,
        }
    )


def _setup_tracer(*, settings: Settings, resource: Resource) -> None:
    tracer_provider = TracerProvider(resource=resource)
    tracer_exporter = OTLPSpanExporter(
        endpoint=settings.otel_grpc_endpoint,
        insecure=True,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(tracer_exporter))
    trace.set_tracer_provider(tracer_provider)


def _setup_metrics(*, settings: Settings, resource: Resource) -> None:
    metric_exporter = OTLPMetricExporter(
        endpoint=settings.otel_grpc_endpoint,
        insecure=True,
    )
    metric_readers = [PeriodicExportingMetricReader(metric_exporter)]
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=metric_readers)
    )


def _setup_logs(*, settings: Settings, resource: Resource) -> None:
    log_exporter = OTLPLogExporter(
        endpoint=settings.otel_grpc_endpoint,
        insecure=True,
    )
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    _logs.set_logger_provider(logger_provider)


def instrument(*, settings: Settings) -> None:
    resource = _resource(settings)
    _setup_tracer(settings=settings, resource=resource)
    _setup_metrics(settings=settings, resource=resource)
    _setup_logs(settings=settings, resource=resource)
    LoggingInstrumentor().instrument()


# Each function below reads the global provider, so a process calls instrument first.
def instrument_app(app: FastAPI) -> None:
    # The ASGI send and receive spans double the rows of each request.
    FastAPIInstrumentor.instrument_app(app, exclude_spans=["receive", "send"])


def instrument_engine(engine: AsyncEngine) -> None:
    # 0.66b1 declares SQLAlchemy < 2.1 and instruments nothing without the skip.
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine, skip_dep_check=True)


def instrument_broker(broker: AsyncBroker) -> None:
    # The middleware carries the trace from the sender to the worker in the labels.
    broker.add_middlewares(OpenTelemetryMiddleware())
