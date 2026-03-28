from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar("T", int, str)


@dataclass(frozen=True,Generic[T])
class Id:
    value: T

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"Id({self.value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Id):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)