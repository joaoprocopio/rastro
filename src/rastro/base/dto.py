import json
from abc import ABC
from dataclasses import dataclass, fields
from typing import Self


@dataclass(frozen=True)
class DTO(ABC):
    @classmethod
    def parse_json(cls, value: str | bytes | bytearray) -> Self:
        data = json.loads(value)  # type: ignore
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})  # type: ignore
