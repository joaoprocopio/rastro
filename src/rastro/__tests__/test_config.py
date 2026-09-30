import pydantic
import pytest

from rastro.config import Settings

SECRET_KEY = "a-secret-key-with-at-least-32-characters"


def test_csv_settings_split_on_commas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RASTRO_ALLOWED_HOSTS", " one, two,three ,")

    settings = Settings.model_validate({"secret_key": SECRET_KEY})

    assert settings.allowed_hosts == ["one", "two", "three"]


def test_secret_key_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RASTRO_SECRET_KEY")

    with pytest.raises(pydantic.ValidationError, match="secret_key"):
        Settings.model_validate({})


def test_short_secret_key_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError, match="secret_key"):
        Settings.model_validate({"secret_key": "short"})


def test_database_url_uses_psycopg3() -> None:
    settings = Settings.model_validate(
        {"secret_key": SECRET_KEY, "postgres_password": "p@ss/word"}
    )

    assert settings.database_url.drivername == "postgresql+psycopg"
    assert settings.database_url.password == "p@ss/word"
