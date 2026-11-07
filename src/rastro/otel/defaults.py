import os
from urllib import parse

from opentelemetry.instrumentation._semconv import OTEL_SEMCONV_STABILITY_OPT_IN
from opentelemetry.instrumentation.logging.environment_variables import (
    OTEL_PYTHON_LOG_HANDLER_LEVEL,
)
from opentelemetry.sdk.environment_variables import (
    OTEL_BLRP_MAX_EXPORT_BATCH_SIZE,
    OTEL_BLRP_MAX_QUEUE_SIZE,
    OTEL_BLRP_SCHEDULE_DELAY,
    OTEL_EXPORTER_OTLP_COMPRESSION,
    OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE,
    OTEL_RESOURCE_ATTRIBUTES,
    OTEL_SERVICE_NAME,
)
from opentelemetry.semconv._incubating.attributes import deployment_attributes
from opentelemetry.semconv.attributes import service_attributes

from rastro.settings import Settings


# The SDK splits on "," and "=" and unquotes each value.
def _resource_attributes(attributes: dict[str, str]) -> str:
    return ",".join(f"{key}={parse.quote(value)}" for key, value in attributes.items())


def defaults(settings: Settings) -> dict[str, str | int]:
    return {
        OTEL_SERVICE_NAME: settings.service_name,
        OTEL_RESOURCE_ATTRIBUTES: _resource_attributes(
            {
                service_attributes.SERVICE_NAMESPACE: settings.service_namespace,
                deployment_attributes.DEPLOYMENT_ID: settings.deployment_id,
                deployment_attributes.DEPLOYMENT_ENVIRONMENT: settings.deployment_environment,
            }
        ),
        # Cumulative re-exports every series seen since start, every interval.
        OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE: "DELTA",
        OTEL_EXPORTER_OTLP_COMPRESSION: "gzip",
        # DEBUG logs reach the console only.
        OTEL_PYTHON_LOG_HANDLER_LEVEL: "INFO",
        OTEL_BLRP_MAX_QUEUE_SIZE: 8_192,
        OTEL_BLRP_MAX_EXPORT_BATCH_SIZE: 1_024,
        OTEL_BLRP_SCHEDULE_DELAY: 2_000,  # ms
        OTEL_SEMCONV_STABILITY_OPT_IN: "http,database",
    }


def apply(settings: Settings) -> None:
    for name, value in defaults(settings).items():
        os.environ.setdefault(name, str(value))
