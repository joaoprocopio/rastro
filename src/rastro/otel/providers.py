from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


# Resource.create sets a service.instance.id, so the delta points of two processes stay two series.
def create_resource() -> Resource:
    return Resource.create()


def _setup_tracer(resource: Resource) -> None:
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)


def _setup_metrics(resource: Resource) -> None:
    metric_readers = [PeriodicExportingMetricReader(OTLPMetricExporter())]
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=metric_readers)
    )


def _setup_logs(resource: Resource) -> None:
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    _logs.set_logger_provider(logger_provider)


def setup(resource: Resource) -> None:
    _setup_tracer(resource)
    _setup_metrics(resource)
    _setup_logs(resource)
