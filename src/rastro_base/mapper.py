from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T_SOURCE = TypeVar("T_SOURCE")
T_TARGET = TypeVar("T_TARGET")


class Mapper(ABC, Generic[T_SOURCE, T_TARGET]):
    @staticmethod
    @abstractmethod
    def map(source: T_SOURCE) -> T_TARGET: ...
