import os
from typing import Callable, TypeVar, overload

T = TypeVar("T")


def cast_env(value, *, caster: Callable[[str], T]) -> T:
    return caster(value)


@overload
def get_env(
    key: str,
    *,
    default: str,
) -> str: ...


@overload
def get_env(
    key: str,
    *,
    default: None = None,
) -> str | None: ...


def get_env(
    key: str,
    *,
    default: str | None = None,
) -> str | None:
    value = os.environ.get(key)

    if value is None:
        return default

    return value
