from abc import ABC
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ValueObject(ABC, Generic[T]):
    value: T

    def validate(self) -> None: ...

    def __post_init__(self) -> None:
        self.validate()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"
