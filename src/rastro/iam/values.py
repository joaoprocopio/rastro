import re
import unicodedata
from dataclasses import dataclass

from rastro.common.values import InvalidValueError, StrValueObject

EMAIL_PATTERN = re.compile(r"^[a-z0-9_.+-]+@[a-z0-9-]+\.[a-z0-9-.]+$")
DISPLAY_NAME_MAX_LENGTH = 320
RAW_PASSWORD_MIN_LENGTH = 8


@dataclass(frozen=True, slots=True)
class Email(StrValueObject):
    def __post_init__(self) -> None:
        value = unicodedata.normalize("NFKC", self.value.strip()).lower()
        if EMAIL_PATTERN.match(value) is None:
            raise InvalidValueError("iam.invalid_email")
        object.__setattr__(self, "value", value)


@dataclass(frozen=True, slots=True)
class DisplayName(StrValueObject):
    def __post_init__(self) -> None:
        value = self.value.strip()
        if len(value) > DISPLAY_NAME_MAX_LENGTH:
            raise InvalidValueError("iam.invalid_display_name")
        object.__setattr__(self, "value", value)


@dataclass(frozen=True, slots=True)
class RawPassword(StrValueObject):
    def __post_init__(self) -> None:
        if len(self.value) < RAW_PASSWORD_MIN_LENGTH:
            raise InvalidValueError("iam.invalid_password")


@dataclass(frozen=True, slots=True)
class HashedPassword(StrValueObject):
    pass
