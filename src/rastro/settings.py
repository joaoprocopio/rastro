from datetime import timedelta
from typing import Annotated, Literal

from pydantic import BeforeValidator, PostgresDsn, Secret, UrlConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

# The scheme names the SQLAlchemy driver, so another driver fails at startup.
PsycopgDsn = Annotated[
    PostgresDsn, UrlConstraints(allowed_schemes=["postgresql+psycopg"])
]

SameSite = Literal["lax", "strict", "none"]


def _seconds(value: object) -> object:
    return int(value) if isinstance(value, str) and value.isdecimal() else value


# Pydantic parses an ISO 8601 duration from text, but not a number of seconds.
Duration = Annotated[timedelta, BeforeValidator(_seconds)]


def _variable(field: str) -> str:
    return f"RASTRO_{field.upper()}"


class Settings(BaseSettings):
    # The alias makes a validation error name the variable, not the field.
    model_config = SettingsConfigDict(
        alias_generator=_variable,
        frozen=True,
        hide_input_in_errors=True,
    )

    openapi_enabled: bool = False

    # No default, so no password sits in the code.
    postgres_url: Secret[PsycopgDsn]

    zeromq_publish_address: str = "tcp://127.0.0.1:5555"
    zeromq_subscribe_address: str = "tcp://127.0.0.1:5555"

    service_namespace: str = "rastro"
    service_name: str = "rastro"
    deployment_id: str = "local"
    deployment_environment: str = "dev"
    otel_grpc_endpoint: str = "localhost:4317"

    session_lifetime: Duration = timedelta(days=14)
    session_cookie_name: str = "rastro_session"
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: SameSite = "lax"
    session_token_bytes: int = 32

    csrf_cookie_name: str = "rastro_csrf"
    csrf_cookie_secure: bool = True
    # Scripts read the token to send it back, so the cookie is not HttpOnly.
    csrf_cookie_httponly: bool = False
    csrf_cookie_samesite: SameSite = "lax"
    csrf_token_bytes: int = 32
    csrf_header_name: str = "X-CSRF-Token"
