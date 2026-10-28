from datetime import timedelta
from pathlib import Path

import pytest

from rastro.auth.domain.value_objects import SessionLifetime
from rastro.common.domain.value_objects import TokenBytes
from rastro.settings import CorsOrigin, SameSite, Settings

ENV_EXAMPLE = Path(__file__).parents[3] / ".env.example"


def _example_variables() -> dict[str, str]:
    lines = ENV_EXAMPLE.read_text().splitlines()
    return dict(line.split("=", 1) for line in lines if line)


def test_env_example_lists_every_variable(empty_environment: None) -> None:
    variables = {field.alias for field in Settings.model_fields.values()}

    assert set(_example_variables()) == variables


def test_env_example_loads(
    empty_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in _example_variables().items():
        monkeypatch.setenv(name, value)

    settings = Settings()

    assert str(settings.postgres_url.get_secret_value()) == (
        "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    )
    assert settings.openapi_enabled is True
    assert settings.cors_allowed_origins == [CorsOrigin("http://localhost:5173")]


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
        ("session_lifetime", SessionLifetime(timedelta(days=14))),
        ("session_cookie_name", "rastro_session"),
        ("session_cookie_secure", True),
        ("session_cookie_httponly", True),
        ("session_cookie_samesite", SameSite.LAX),
        ("session_token_bytes", TokenBytes(32)),
        ("csrf_cookie_name", "rastro_csrf"),
        ("csrf_cookie_secure", True),
        ("csrf_cookie_httponly", False),
        ("csrf_cookie_samesite", SameSite.LAX),
        ("csrf_token_bytes", TokenBytes(32)),
        ("csrf_header_name", "X-CSRF-Token"),
        ("cors_allowed_origins", []),
        ("cors_allowed_origin_regex", None),
        (
            "cors_allow_methods",
            ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"],
        ),
        (
            "cors_allow_headers",
            [
                "accept",
                "authorization",
                "content-type",
                "user-agent",
                "x-csrftoken",
                "x-csrf-token",
                "x-requested-with",
            ],
        ),
        ("cors_expose_headers", []),
        ("cors_preflight_max_age", timedelta(minutes=10)),
        ("cors_allow_credentials", True),
        ("cors_allow_private_network", False),
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


def test_the_session_lifetime_reads_an_iso_8601_duration(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RASTRO_SESSION_LIFETIME", "PT1H")

    assert Settings().session_lifetime == SessionLifetime(timedelta(hours=1))


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ("PT0S", "greater_than"),
        ("-PT1H", "greater_than"),
        ("3600", "time_delta_parsing"),
    ],
)
def test_a_session_lifetime_that_is_not_a_positive_duration_stops_the_settings(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch, value: str, error: str
) -> None:
    monkeypatch.setenv("RASTRO_SESSION_LIFETIME", value)

    with pytest.raises(
        ValueError, match=rf"(?m)^RASTRO_SESSION_LIFETIME\n  .* \[type={error}\]"
    ):
        Settings()


@pytest.mark.parametrize(
    "name", ["RASTRO_SESSION_TOKEN_BYTES", "RASTRO_CSRF_TOKEN_BYTES"]
)
def test_a_token_size_of_16_bytes_loads(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.setenv(name, "16")

    assert getattr(Settings(), name.removeprefix("RASTRO_").lower()) == TokenBytes(16)


@pytest.mark.parametrize(
    "name", ["RASTRO_SESSION_TOKEN_BYTES", "RASTRO_CSRF_TOKEN_BYTES"]
)
def test_a_token_size_under_16_bytes_stops_the_settings(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.setenv(name, "15")

    with pytest.raises(
        ValueError,
        match=rf"(?m)^{name}\n  .* \[type=greater_than_equal\]",
    ):
        Settings()


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


def test_a_list_of_cors_origins_loads(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "RASTRO_CORS_ALLOWED_ORIGINS",
        '["http://localhost:5173", "https://rastro.example:8443"]',
    )

    assert Settings().cors_allowed_origins == [
        CorsOrigin("http://localhost:5173"),
        CorsOrigin("https://rastro.example:8443"),
    ]


@pytest.mark.parametrize(
    "origin",
    ["http://localhost:5173", "http://localhost:5173/", "http://localhost:5173/path"],
)
def test_a_cors_origin_loads_unchanged(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch, origin: str
) -> None:
    monkeypatch.setenv("RASTRO_CORS_ALLOWED_ORIGINS", f'["{origin}"]')

    assert [str(loaded) for loaded in Settings().cors_allowed_origins] == [origin]


def test_a_cors_origin_loads_without_the_default_port_of_its_scheme(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RASTRO_CORS_ALLOWED_ORIGINS", '["https://x.com:443"]')

    assert [str(loaded) for loaded in Settings().cors_allowed_origins] == [
        "https://x.com"
    ]


@pytest.mark.parametrize(
    "origin", ["localhost:5173", "ftp://x.com", "http://localhost:99999"]
)
def test_a_cors_origin_with_no_scheme_another_scheme_or_a_bad_port_stops_the_settings(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch, origin: str
) -> None:
    monkeypatch.setenv("RASTRO_CORS_ALLOWED_ORIGINS", f'["{origin}"]')

    with pytest.raises(ValueError, match=r"(?m)^RASTRO_CORS_ALLOWED_ORIGINS\.0\n  "):
        Settings()


def test_a_cors_origin_regex_loads_unchanged(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "RASTRO_CORS_ALLOWED_ORIGIN_REGEX", r"https://[a-z]+\.example\.com"
    )

    assert Settings().cors_allowed_origin_regex == r"https://[a-z]+\.example\.com"


def test_a_wildcard_in_the_cors_methods_loads(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RASTRO_CORS_ALLOW_METHODS", '["*"]')

    assert Settings().cors_allow_methods == ["*"]


def test_a_cors_method_with_a_typo_stops_the_settings(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RASTRO_CORS_ALLOW_METHODS", '["PSOT"]')

    with pytest.raises(ValueError, match=r"(?m)^RASTRO_CORS_ALLOW_METHODS\.0\."):
        Settings()


def test_the_cors_preflight_max_age_reads_an_iso_8601_duration(
    postgres_url_only: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RASTRO_CORS_PREFLIGHT_MAX_AGE", "PT1H")

    assert Settings().cors_preflight_max_age == timedelta(hours=1)
