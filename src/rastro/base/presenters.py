from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T_PRIVATE = TypeVar("T_PRIVATE")
T_PUBLIC = TypeVar("T_PUBLIC")


class Presenter(ABC, Generic[T_PRIVATE, T_PUBLIC]):
    @staticmethod
    @abstractmethod
    def present(private: T_PRIVATE) -> T_PUBLIC: ...
