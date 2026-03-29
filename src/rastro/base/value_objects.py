from abc import ABC
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ValueObject(ABC, Generic[T]):
    value: T = field()
