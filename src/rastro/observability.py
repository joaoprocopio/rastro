import logging
from typing import cast

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
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

resource = Resource(
    attributes={
        service_attributes.SERVICE_NAME: settings.SERVICE_NAME,
        deployment_attributes.DEPLOYMENT_ID: settings.DEPLOYMENT_ID,
        deployment_attributes.DEPLOYMENT_ENVIRONMENT: settings.DEPLOYMENT_ENVIRONMENT,
    }
)


def instrument() -> None:
    tracer_provider = TracerProvider(resource=resource)

    tracer_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_GRPC_ENDPOINT,
        insecure=True,
    )
    tracer_processor = BatchSpanProcessor(tracer_exporter)
    tracer_provider.add_span_processor(tracer_processor)

    trace.set_tracer_provider(tracer_provider)

    def response_hook(
        span: trace.Span, request: WSGIRequest, response: HttpResponse
    ) -> None:
        if request.user.id is not None and request.user.is_authenticated:
            span.set_attribute("user.id", request.user.pk)
            span.set_attribute(
                "user.email",
                cast(str, getattr(request.user, request.user.get_email_field_name())),
            )

    DjangoInstrumentor().instrument(response_hook=response_hook)

    logger.info("OpenTelemetry Django initialized with OTLP exporter")
