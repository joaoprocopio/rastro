from abc import ABC, abstractmethod
from typing import Self


class FromStr(ABC):
    @classmethod
    @abstractmethod
    def from_str(cls, value: str | bytes | bytearray) -> Self: ...
