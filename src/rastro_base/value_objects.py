from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ValueObject(ABC, Generic[T]):
    @property
    @abstractmethod
    def value(self) -> T: ...

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"

    def __eq__(self, other: Any) -> bool:
        return self.value == other.value if isinstance(other, ValueObject) else False

    def __hash__(self) -> int:
        return hash(self.value)
