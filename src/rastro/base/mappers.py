from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T_INPUT = TypeVar("T_INPUT")
T_OUTPUT = TypeVar("T_OUTPUT")


class Mapper(ABC, Generic[T_INPUT, T_OUTPUT]):
    @staticmethod
    @abstractmethod
    def map(input: T_INPUT) -> T_OUTPUT: ...
