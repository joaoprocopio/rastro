import logging
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv._incubating.attributes import deployment_attributes
from opentelemetry.semconv.attributes import service_attributes

from rastro.config import DeploymentConfig


logger = logging.getLogger(__name__)


class OTelTelemetryService:
    def __init__(self, config: DeploymentConfig):
        self._config = config
        self._tracer_provider: TracerProvider | None = None

    def initialize(self) -> None:
        resource = Resource(
            attributes={
                service_attributes.SERVICE_NAME: "rastro",
                deployment_attributes.DEPLOYMENT_ID: self._config.id,
                deployment_attributes.DEPLOYMENT_ENVIRONMENT: self._config.environment,
            }
        )

        self._tracer_provider = TracerProvider(resource=resource)
        tracer_provider = TracerProvider(resource=resource)

        tracer_exporter = OTLPSpanExporter(
            endpoint=f"http://{self._config.id}:4317",
            insecure=True,
        )
        tracer_processor = BatchSpanProcessor(tracer_exporter)
        tracer_provider.add_span_processor(tracer_processor)
        trace.set_tracer_provider(tracer_provider)

        DjangoInstrumentor().instrument(response_hook=self._response_hook)

        logger.info("OpenTelemetry Django initialized with OTLP exporter")

    def _response_hook(self, span, request, response):
        if request.user.is_authenticated:
            span.set_attribute("user.id", request.user.pk)
            span.set_attribute(
                "user.email", getattr(request.user, request.user.EMAIL_FIELD)
            )
            span.set_attribute("user.full_name", request.user.get_full_name())

    def shutdown(self) -> None:
        if self._tracer_provider:
            self._tracer_provider.shutdown()

    def record_request(
        self, request_id: str, path: str, method: str, status_code: int
    ) -> None:
        pass

    def record_error(self, request_id: str, error: Exception) -> None:
        pass

    def set_user_context(self, user_id: int, email: str) -> None:
        pass
