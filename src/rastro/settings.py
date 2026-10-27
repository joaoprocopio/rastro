from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


def _variable(field: str) -> str:
    return f"RASTRO_{field.upper()}"


class Settings(BaseSettings):
    # The alias makes a validation error name the variable, not the field.
    model_config = SettingsConfigDict(
        alias_generator=_variable,
        frozen=True,
        hide_input_in_errors=True,
    )

    openapi_enabled: bool

    # The scheme names the driver, for example postgresql+psycopg.
    postgres_url: PostgresDsn

    zeromq_publish_address: str
    zeromq_subscribe_address: str

    service_namespace: str
    service_name: str
    deployment_id: str
    deployment_environment: str
    otel_grpc_endpoint: str
