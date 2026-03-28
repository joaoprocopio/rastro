import os
from pydantic import TypeAdapter, ValidationError

from rastro.shared.domain.value_objects import Csv


def validate_bool(value: str) -> bool:
    return TypeAdapter(bool).validate_strings(value)


def validate_csv(value: str) -> list[str]:
    return TypeAdapter(Csv).validate_strings(value)


def get_env(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} is required")
    return value


def get_env_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return validate_bool(value)


def get_env_csv(key: str, default: str = "") -> list[str]:
    value = os.getenv(key, default)
    return validate_csv(value) if value else []
