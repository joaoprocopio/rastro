import os
from typing import Callable, TypeVar, overload

T = TypeVar("T")


@overload
def get_env(
    key: str,
    *,
    cast: Callable[[str], T],
    default: T,
) -> T: ...


@overload
def get_env(
    key: str,
    *,
    cast: Callable[[str], T],
    default: None = None,
) -> T | None: ...


def get_env(
    key: str,
    *,
    cast: Callable[[str], T],
    default: T | None = None,
) -> T | None:
    value = os.environ.get(key)

    if value is None:
        return default

    return cast(value)
