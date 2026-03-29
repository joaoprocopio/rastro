import re
from dataclasses import dataclass

from rastro_base.value_objects import ValueObject

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True)
class Email(ValueObject[str]):
    value: str

    def __post_init__(self):
        if not EMAIL_PATTERN.match(self.value):
            raise ValueError(f"Invalid email: {self.value}")
