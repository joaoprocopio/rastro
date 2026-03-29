from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ValueObject(ABC, Generic[T]):
    value: T

    @abstractmethod
    def validate(self) -> None: ...

    def __post_init__(self) -> None:
        self.validate()
