import logging
import os

from opentelemetry.sdk.environment_variables import OTEL_EXPORTER_OTLP_ENDPOINT

from rastro.otel import defaults, instrumentors, providers
from rastro.otel.instrumentors import instrument_app, instrument_engine
from rastro.settings import Settings

__all__ = ["instrument", "instrument_app", "instrument_engine"]

logger = logging.getLogger(__name__)


def instrument(*, settings: Settings) -> None:
    defaults.apply(settings)

    # With no endpoint, every batch would fail against the exporter's localhost default.
    if not os.environ.get(OTEL_EXPORTER_OTLP_ENDPOINT):
        logger.warning("OpenTelemetry is disabled")
        return

    providers.setup(providers.create_resource())
    instrumentors.instrument_all()
