from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class UseCase(ABC, Generic[TInput, TOutput]):
    @abstractmethod
    def execute(self, input: TInput) -> TOutput: ...
