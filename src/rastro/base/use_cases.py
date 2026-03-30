from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T_IN = TypeVar("T_IN")
T_OUT = TypeVar("T_OUT")


class UseCase(ABC, Generic[T_IN, T_OUT]):
    @abstractmethod
    def execute(self, input: T_IN) -> T_OUT: ...
