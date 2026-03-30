from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T_INPUT = TypeVar("T_INPUT")
T_OUTPUT = TypeVar("T_OUTPUT")


class UseCase(ABC, Generic[T_INPUT, T_OUTPUT]):
    @abstractmethod
    def execute(self, input: T_INPUT) -> T_OUTPUT: ...
