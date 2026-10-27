import os
from pathlib import Path

import pytest

from rastro.settings import Settings

ENV_EXAMPLE = Path(__file__).parents[3] / ".env.example"


def _example_variables() -> dict[str, str]:
    lines = ENV_EXAMPLE.read_text().splitlines()
    return dict(line.split("=", 1) for line in lines if line)


@pytest.fixture
def example_environment(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    for name in os.environ:
        if name.startswith("RASTRO_"):
            monkeypatch.delenv(name)
    variables = _example_variables()
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    return variables


def test_env_example_declares_every_setting(example_environment: None) -> None:
    settings = Settings()

    assert str(settings.postgres_url) == (
        "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    )
    assert settings.openapi_enabled is True


@pytest.mark.parametrize("name", sorted(_example_variables()))
def test_a_missing_variable_stops_the_settings_with_its_name(
    example_environment: None, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.delenv(name)

    with pytest.raises(ValueError, match=rf"(?m)^{name}\n  Field required"):
        Settings()


def test_a_malformed_postgres_url_stops_the_settings_with_its_name(
    example_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RASTRO_POSTGRES_URL", "not-a-url")

    with pytest.raises(ValueError, match=r"(?m)^RASTRO_POSTGRES_URL\n  Input"):
        Settings()


def test_the_error_hides_the_values_it_read(
    example_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RASTRO_POSTGRES_URL", "postgres:hunter2-secret@localhost")

    with pytest.raises(ValueError) as excinfo:
        Settings()

    assert "hunter2-secret" not in str(excinfo.value)
