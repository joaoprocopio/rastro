from datetime import timedelta
from enum import StrEnum
from http import HTTPMethod
from typing import Annotated, Literal

from pydantic import Field, HttpUrl, PostgresDsn, Secret, SecretStr, UrlConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

from rastro.auth.domain.value_objects import (
    Email,
    ResetLinkUrl,
    ResetTokenCooldown,
    ResetTokenLifetime,
    SessionLifetime,
)
from rastro.common.domain.value_objects import TokenBytes


# The scheme names the SQLAlchemy driver, so another driver fails at startup.
class PsycopgDsn(PostgresDsn):
    _constraints = UrlConstraints(
        host_required=True, allowed_schemes=["postgresql+psycopg"]
    )


# A browser sends an origin with no trailing slash, so the empty path stays empty.
class CorsOrigin(HttpUrl):
    _constraints = UrlConstraints(
        allowed_schemes=["http", "https"], host_required=True, preserve_empty_path=True
    )


class SameSite(StrEnum):
    LAX = "lax"
    STRICT = "strict"
    NONE = "none"


class SmtpSecurity(StrEnum):
    NONE = "none"
    STARTTLS = "starttls"
    TLS = "tls"


def _variable(field: str) -> str:
    return f"RASTRO_{field.upper()}"


class Settings(BaseSettings):
    # The alias makes a validation error name the variable, not the field.
    model_config = SettingsConfigDict(
        alias_generator=_variable,
        # An env file also holds the OTEL_* variables, which the SDK reads, and the ports, which compose reads.
        extra="ignore",
        # An env file holds a line for every setting, so an empty line means unset.
        env_ignore_empty=True,
        frozen=True,
        hide_input_in_errors=True,
    )

    openapi_enabled: bool = False

    # No default, so no password sits in the code.
    postgres_url: Secret[PsycopgDsn]

    service_namespace: str = "rastro"
    service_name: str = "rastro"
    deployment_id: str = "local"
    deployment_environment: str = "dev"

    session_lifetime: SessionLifetime = SessionLifetime(timedelta(days=14))
    session_cookie_name: str = "rastro_session"
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: SameSite = SameSite.LAX
    session_token_bytes: TokenBytes = TokenBytes(32)

    csrf_cookie_name: str = "rastro_csrf"
    csrf_cookie_secure: bool = True
    # Scripts read the token to send it back, so the default is not HttpOnly.
    csrf_cookie_httponly: bool = False
    csrf_cookie_samesite: SameSite = SameSite.LAX
    csrf_token_bytes: TokenBytes = TokenBytes(32)
    csrf_header_name: str = "X-CSRF-Token"

    smtp_host: str = "localhost"
    smtp_port: Annotated[int, Field(ge=1, le=65535)] = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_security: SmtpSecurity = SmtpSecurity.STARTTLS
    smtp_sender: Email = Email("no-reply@rastro.example")
    smtp_timeout: Annotated[timedelta, Field(gt=timedelta(0))] = timedelta(seconds=60)

    # A relay with click tracking rewrites the link and reads the token, so turn it off.
    reset_link_url: ResetLinkUrl = ResetLinkUrl("http://localhost:5173/password-reset")
    reset_token_lifetime: ResetTokenLifetime = ResetTokenLifetime(timedelta(hours=1))
    reset_token_cooldown: ResetTokenCooldown = ResetTokenCooldown(timedelta(seconds=60))
    reset_token_bytes: TokenBytes = TokenBytes(32)

    # Empty, so a deployment that forgets the variable allows no other origin.
    cors_allowed_origins: list[CorsOrigin] = []
    cors_allowed_origin_regex: str | None = None
    cors_allow_methods: list[HTTPMethod | Literal["*"]] = [
        HTTPMethod.DELETE,
        HTTPMethod.GET,
        HTTPMethod.OPTIONS,
        HTTPMethod.PATCH,
        HTTPMethod.POST,
        HTTPMethod.PUT,
    ]
    cors_allow_headers: list[str] = [
        "accept",
        "authorization",
        "content-type",
        "user-agent",
        "x-csrftoken",
        "x-csrf-token",
        "x-requested-with",
    ]
    cors_expose_headers: list[str] = []
    cors_preflight_max_age: timedelta = timedelta(minutes=10)
    cors_allow_credentials: bool = True
    cors_allow_private_network: bool = False
