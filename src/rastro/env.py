import os
from typing import Callable, Optional, TypeVar, overload

T = TypeVar("T")


@overload
def get_env(
    key: str,
    *,
    default: None = None,
    parser: None = None,
) -> Optional[str]: ...


@overload
def get_env(
    key: str,
    *,
    default: str,
    parser: None = None,
) -> str: ...


@overload
def get_env(
    key: str,
    *,
    default: None = None,
    parser: Callable[[str], T],
) -> Optional[T]: ...


@overload
def get_env(
    key: str,
    *,
    default: str,
    parser: Callable[[str], T],
) -> T: ...


def get_env(
    key: str,
    *,
    default: Optional[str] = None,
    parser: Optional[Callable[[str], T]] = None,
) -> Optional[str | T]:
    value = os.environ.get(key)

    if value is None:
        if parser is not None and default is not None:
            return parser(default)
        return default

    if parser is not None:
        return parser(value)

    return value


def parse_csv(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split(",")]


def parse_booleanish(raw_value: str) -> bool:
    value = raw_value.lower()

    if value == "true" or value == "1":
        return True

    if value == "false" or value == "0":
        return False

    raise TypeError(f"Could not parse {raw_value} as booleanish value.")
