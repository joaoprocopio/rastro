from dataclasses import dataclass

from rastro_base.value_objects import ValueObject


@dataclass(frozen=True)
class Id(ValueObject[int]):
    def __post_init__(self):
        if not self.value >= 1:
            raise ValueError(f"ID must be greater or equal than 1, got {self.value}")
