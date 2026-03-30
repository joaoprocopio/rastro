import html
from dataclasses import asdict, fields, is_dataclass
from typing import TypeVar

from rastro.base.value_objects import ValueObject


def sanitize_string(value: str, max_length: int | None = None) -> str:
    stripped = value.strip()
    if max_length is not None and len(stripped) > max_length:
        raise ValueError(f"Value exceeds max length of {max_length}")
    return stripped


def sanitize_email(value: str) -> str:
    return value.strip().lower()


def sanitize_html(value: str) -> str:
    return html.escape(value)


def sanitize_username(value: str, max_length: int = 50) -> str:
    sanitized = sanitize_string(value, max_length=max_length)
    if not sanitized:
        raise ValueError("Username cannot be empty")
    if not all(c.isalnum() or c == "_" for c in sanitized):
        raise ValueError(
            "Username can only contain alphanumeric characters and underscores"
        )
    return sanitized


T = TypeVar("T")


def entity_to_dict(
    entity: object, exclude: set[str] | None = None
) -> dict[str, object]:
    exclude = exclude or set()
    result: dict[str, object] = {}

    if not is_dataclass(entity):
        raise TypeError("entity must be a dataclass instance")

    for field in fields(entity):  # type: ignore[misc]
        field_name = field.name  # type: ignore[misc]
        if field_name in exclude:
            continue
        value = getattr(entity, field_name)  # type: ignore[misc]
        result[field_name] = _unwrap_value(value)  # type: ignore[misc]

    return result


def _unwrap_value(value: object) -> object:
    if isinstance(value, ValueObject):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):  # type: ignore[misc]
        return entity_to_dict(value)
    if isinstance(value, list):
        return [_unwrap_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _unwrap_value(v) for k, v in value.items()}  # type: ignore[misc]
    return value
