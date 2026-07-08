from enum import StrEnum
from typing import TypeVar

E = TypeVar("E", bound=StrEnum)


def str_enum_to_choices(str_enum: type[E]) -> list[tuple[str, str]]:
    return [(member.value, member.name) for member in str_enum]
