import os
from datetime import timedelta
from pathlib import Path

import pytest

from rastro.settings import Settings

ENV_EXAMPLE = Path(__file__).parents[3] / ".env.example"
POSTGRES_URL = "postgresql+psycopg://postgres:hunter2-secret@localhost:5432/postgres"


def _example_variables() -> dict[str, str]:
    lines = ENV_EXAMPLE.read_text().splitlines()
    return dict(line.split("=", 1) for line in lines if line)


@pytest.fixture
def empty_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in os.environ:
        if name.startswith("RASTRO_"):
            monkeypatch.delenv(name)


@pytest.fixture
def postgres_url_only(empty_environment: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RASTRO_POSTGRES_URL", POSTGRES_URL)


def test_env_example_lists_every_variable(empty_environment: None) -> None:
    variables = {field.alias for field in Settings.model_fields.values()}

    assert set(_example_variables()) == variables


def test_env_example_loads(
    empty_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in _example_variables().items():
        monkeypatch.setenv(name, value)

    settings = Settings()

    assert settings.postgres_url.get_secret_value().unicode_string() == (
        "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    )
    assert settings.openapi_enabled is True


@pytest.mark.parametrize(
    ("field", "default"),
    [
        ("openapi_enabled", False),
        ("zeromq_publish_address", "tcp://127.0.0.1:5555"),
        ("zeromq_subscribe_address", "tcp://127.0.0.1:5555"),
        ("service_namespace", "rastro"),
        ("service_name", "rastro"),
        ("deployment_id", "local"),
        ("deployment_environment", "dev"),
        ("otel_grpc_endpoint", "localhost:4317"),
        ("session_lifetime", timedelta(days=14)),
        ("session_cookie_name", "rastro_session"),
        ("session_cookie_secure", True),
        ("session_cookie_httponly", True),
        ("session_cookie_samesite", "lax"),
        ("session_token_bytes", 32),
        ("csrf_cookie_name", "rastro_csrf"),
        ("csrf_cookie_secure", True),
        ("csrf_cookie_httponly", False),
        ("csrf_cookie_samesite", "lax"),
        ("csrf_token_bytes", 32),
        ("csrf_header_name", "X-CSRF-Token"),
    ],
)
def test_a_setting_without_its_variable_takes_its_default(
    postgres_url_only: None, field: str, default: object
) -> None:
    settings = Settings()

    assert getattr(settings, field) == default


def test_every_setting_but_the_postgres_url_has_a_default() -> None:
    required = [
        field.alias for field in Settings.model_fields.values() if field.is_required()
    ]

    assert required == ["RASTRO_POSTGRES_URL"]


@pytest.mark.parametrize(
    ("value", "lifetime"),
    [("P1D", timedelta(days=1)), ("3600", timedelta(hours=1))],
)
def test_the_session_lifetime_reads_a_duration_or_seconds(
    postgres_url_only: None,
    monkeypatch: pytest.MonkeyPatch,
    value: str,
    lifetime: timedelta,
) -> None:
    monkeypatch.setenv("RASTRO_SESSION_LIFETIME", value)

    assert Settings().session_lifetime == lifetime


@pytest.mark.parametrize(
    "name", ["RASTRO_SESSION_COOKIE_SAMESITE", "RASTRO_CSRF_COOKIE_SAMESITE"]
)
@pytest.mark.parametrize("value", ["lax", "strict", "none"])
def test_a_samesite_setting_accepts_each_policy(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    settings = Settings()

    assert getattr(settings, name.removeprefix("RASTRO_").lower()) == value


@pytest.mark.parametrize(
    "name", ["RASTRO_SESSION_COOKIE_SAMESITE", "RASTRO_CSRF_COOKIE_SAMESITE"]
)
def test_a_samesite_setting_rejects_another_policy(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.setenv(name, "always")

    with pytest.raises(ValueError, match=rf"(?m)^{name}\n  Input"):
        Settings()


def test_a_missing_postgres_url_stops_the_settings_with_its_name(
    empty_environment: None,
) -> None:
    with pytest.raises(ValueError, match=r"(?m)^RASTRO_POSTGRES_URL\n  Field required"):
        Settings()


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://postgres:postgres@localhost:5432/postgres",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        "not-a-url",
    ],
)
def test_a_postgres_url_without_the_psycopg_scheme_stops_the_settings_with_its_name(
    empty_environment: None, monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    monkeypatch.setenv("RASTRO_POSTGRES_URL", url)

    with pytest.raises(ValueError, match=r"(?m)^RASTRO_POSTGRES_URL\n  "):
        Settings()


def test_the_error_hides_the_values_it_read(
    empty_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RASTRO_POSTGRES_URL", "postgres:hunter2-secret@localhost")

    with pytest.raises(ValueError) as excinfo:
        Settings()

    assert "hunter2-secret" not in str(excinfo.value)


def test_the_repr_hides_the_database_password(postgres_url_only: None) -> None:
    assert "hunter2-secret" not in repr(Settings())
