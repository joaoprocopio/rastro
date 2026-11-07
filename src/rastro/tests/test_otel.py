import json
import logging
import os
import subprocess
import sys

import pytest
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.sdk.environment_variables import (
    OTEL_EXPORTER_OTLP_ENDPOINT,
    OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE,
    OTEL_RESOURCE_ATTRIBUTES,
    OTEL_SERVICE_NAME,
)
from opentelemetry.sdk.resources import OTELResourceDetector
from opentelemetry.semconv._incubating.attributes import deployment_attributes
from opentelemetry.semconv.attributes import service_attributes

from rastro import otel
from rastro.otel import defaults, instrumentors
from rastro.settings import Settings
from rastro.tests.conftest import POSTGRES_URL

# Each process sets its global providers once, so this script runs in its own process.
INSTRUMENT_SCRIPT = """
import json
import logging
from opentelemetry import trace
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from rastro import otel
from rastro.settings import Settings

otel.instrument(settings=Settings())
provider = trace.get_tracer_provider()
processor = provider._active_span_processor._span_processors[0]
exporter = processor.span_exporter
print(json.dumps({
    "attributes": dict(provider.resource.attributes),
    "endpoint": exporter._endpoint,
    "compression": exporter._compression.name,
    "handler_levels": [
        handler.level
        for handler in logging.getLogger().handlers
        if isinstance(handler, LoggingHandler)
    ],
}))
"""


def _settings(**values: str) -> Settings:
    return Settings.model_validate({"RASTRO_POSTGRES_URL": POSTGRES_URL, **values})


def _run_instrument_script(**environment: str) -> dict[str, object]:
    kept = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("OTEL_", "RASTRO_"))
    }
    result = subprocess.run(
        [sys.executable, "-c", INSTRUMENT_SCRIPT],
        env={**kept, "RASTRO_POSTGRES_URL": POSTGRES_URL, **environment},
        capture_output=True,
        text=True,
        check=True,
    )
    output: dict[str, object] = json.loads(result.stdout)
    return output


@pytest.fixture
def no_otel_variables(empty_environment: None, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in [OTEL_EXPORTER_OTLP_ENDPOINT, *defaults.defaults(_settings())]:
        monkeypatch.delenv(name, raising=False)


def test_the_resource_reads_a_setting_with_a_comma_and_an_equals_sign_back(
    no_otel_variables: None,
) -> None:
    defaults.apply(_settings(RASTRO_DEPLOYMENT_ID="a,b=c"))

    attributes = OTELResourceDetector().detect().attributes
    assert attributes[deployment_attributes.DEPLOYMENT_ID] == "a,b=c"
    assert attributes[service_attributes.SERVICE_NAME] == "rastro"


def test_a_variable_from_the_environment_overrides_its_default(
    no_otel_variables: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(OTEL_SERVICE_NAME, "operator")
    monkeypatch.setenv(OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE, "CUMULATIVE")

    defaults.apply(_settings(RASTRO_SERVICE_NAME="rastro-worker"))

    assert os.environ[OTEL_SERVICE_NAME] == "operator"
    assert os.environ[OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE] == "CUMULATIVE"
    assert OTEL_RESOURCE_ATTRIBUTES in os.environ


def test_no_endpoint_disables_the_export_and_adds_no_log_handler(
    no_otel_variables: None, caplog: pytest.LogCaptureFixture
) -> None:
    otel.instrument(settings=_settings())

    assert "OpenTelemetry is disabled" in caplog.messages
    handlers = logging.getLogger().handlers
    assert not any(isinstance(handler, LoggingHandler) for handler in handlers)


def test_the_log_handler_drops_debug(no_otel_variables: None) -> None:
    defaults.apply(_settings())

    instrumentors.instrument_all()

    try:
        handlers = [
            handler
            for handler in logging.getLogger().handlers
            if isinstance(handler, LoggingHandler)
        ]
        assert [handler.level for handler in handlers] == [logging.INFO]
    finally:
        instrumentors.uninstrument_all()


def test_an_endpoint_enables_the_export_with_the_defaults() -> None:
    output = _run_instrument_script(
        OTEL_EXPORTER_OTLP_ENDPOINT="http://collector:4318",
        RASTRO_SERVICE_NAME="rastro-worker",
    )

    assert output["endpoint"] == "http://collector:4318/v1/traces"
    assert output["compression"] == "GZIP"
    assert output["handler_levels"] == [logging.INFO]
    attributes = output["attributes"]
    assert isinstance(attributes, dict)
    assert attributes[service_attributes.SERVICE_NAME] == "rastro-worker"
    assert attributes[service_attributes.SERVICE_NAMESPACE] == "rastro"
    assert attributes[deployment_attributes.DEPLOYMENT_ENVIRONMENT] == "dev"
    assert attributes[service_attributes.SERVICE_INSTANCE_ID]


def test_an_https_endpoint_from_the_environment_uses_tls() -> None:
    output = _run_instrument_script(
        OTEL_EXPORTER_OTLP_ENDPOINT="https://collector:4318"
    )

    assert output["endpoint"] == "https://collector:4318/v1/traces"
