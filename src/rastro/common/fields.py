from collections.abc import Sequence
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.core.exceptions import ValidationError
from django.db import models

E = TypeVar("E", bound=StrEnum)


def str_enum_to_choices(str_enum: type[E]) -> list[tuple[str, str]]:
    return [(member.value, member.name) for member in str_enum]


if TYPE_CHECKING:
    _CharField = models.CharField[E, E]
else:
    # Django's Field has no __class_getitem__, so the runtime base adds one through Generic.
    class _CharField(models.CharField, Generic[E]):
        pass


class StrEnumField(_CharField[E]):
    def __init__(self, enum: type[E], **kwargs: Any) -> None:
        self.enum = enum
        kwargs["choices"] = str_enum_to_choices(enum)
        kwargs["max_length"] = max(len(member.value) for member in enum)
        super().__init__(**kwargs)

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        del kwargs["choices"]
        del kwargs["max_length"]
        kwargs["enum"] = self.enum
        return name, path, args, kwargs

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> E | None:
        if value is None:
            return None
        return self.enum(value)

    def to_python(self, value: Any) -> E | None:
        if value is None:
            return None
        try:
            return self.enum(value)
        except ValueError as error:
            raise ValidationError(str(error), code="invalid_choice") from error

    def get_prep_value(self, value: Any) -> str | None:
        if value is None:
            return None
        return self.enum(value).value
