from dataclasses import dataclass

from rastro.common.values import InvalidValueError, StrValueObject


@dataclass(frozen=True, slots=True)
class Color(StrValueObject):
    def __post_init__(self) -> None:
        if self.value not in {"red", "blue"}:
            raise InvalidValueError("sample.invalid_color")
