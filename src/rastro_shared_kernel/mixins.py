import json
from abc import ABC, abstractmethod
from dataclasses import fields
from typing import Self


class FromJson(ABC):
    @classmethod
    def from_json(cls, value: str | bytes | bytearray) -> Self:
        data = json.loads(value)  # type: ignore
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})  # type: ignore


class Validate(ABC):
    @abstractmethod
    def validate(self) -> Self: ...


class Normalize(ABC):
    @abstractmethod
    def normalize(self) -> Self: ...
