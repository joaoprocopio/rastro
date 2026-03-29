import re
from dataclasses import dataclass

from django.core.validators import validate_email

from rastro_base.value_objects import ValueObject

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True)
class Email(ValueObject[str]):
    def __post_init__(self):
        if not validate_email(self.value):
            raise ValueError(f"Invalid email: {self.value}")
