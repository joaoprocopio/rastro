import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv._incubating.attributes import deployment_attributes
from opentelemetry.semconv.attributes import service_attributes

from rastro import settings

logger = logging.getLogger(__name__)


def instrument() -> None:
    resource = Resource(
        attributes={
            service_attributes.SERVICE_NAME: settings.SERVICE_NAME,
            deployment_attributes.DEPLOYMENT_ID: settings.DEPLOYMENT_ID,
            deployment_attributes.DEPLOYMENT_ENVIRONMENT: settings.DEPLOYMENT_ENVIRONMENT,
        }
    )

    tracer_provider = TracerProvider(resource=resource)

    tracer_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_GRPC_ENDPOINT,
        insecure=True,
    )
    tracer_processor = BatchSpanProcessor(tracer_exporter)
    tracer_provider.add_span_processor(tracer_processor)

    trace.set_tracer_provider(tracer_provider)

    # def response_hook(span, request: HttpRequest, response: HttpResponse) -> None:
    #     if request.user.is_authenticated:
    #         span.set_attribute("user.id", request.user.pk)
    #         span.set_attribute(
    #             "user.email", getattr(request.user, request.user.EMAIL_FIELD)
    #         )
    #         span.set_attribute("user.full_name", request.user.get_full_name())

    # response_hook=response_hook
    DjangoInstrumentor().instrument()

    logger.info("OpenTelemetry Django initialized with OTLP exporter")
