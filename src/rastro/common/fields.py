from collections.abc import Sequence
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.core.exceptions import ValidationError
from django.db import models

from rastro.common.values import InvalidValueError, StrValueObject

T = TypeVar("T")
E = TypeVar("E", bound=StrEnum)
V = TypeVar("V", bound=StrValueObject)


def str_enum_to_choices(str_enum: type[E]) -> list[tuple[str, str]]:
    return [(member.value, member.name) for member in str_enum]


def parse_value_object(value_object: type[V], value: str | V) -> V:
    if isinstance(value, value_object):
        return value
    try:
        return value_object(str(value))
    except InvalidValueError as error:
        raise ValidationError(str(error), code=error.code) from error


if TYPE_CHECKING:
    _CharField = models.CharField[T, T]
else:
    # Django's Field has no __class_getitem__, so the runtime base adds one through Generic.
    class _CharField(models.CharField, Generic[T]):
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


class StrValueObjectField(_CharField[V]):
    value_object: type[V]

    def __init__(self, value_object: type[V] | None = None, **kwargs: Any) -> None:
        # A subclass names its value object as a class attribute and takes no argument.
        if value_object is not None:
            self.value_object = value_object
        super().__init__(**kwargs)

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        if "value_object" in vars(self):
            kwargs["value_object"] = self.value_object
        return name, path, args, kwargs

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> V | None:
        if value is None:
            return None
        return self.value_object(value)

    def to_python(self, value: Any) -> V | None:
        if value is None:
            return None
        parsed: V = parse_value_object(self.value_object, value)
        return parsed

    def get_prep_value(self, value: Any) -> str | None:
        if value is None:
            return None
        parsed: V = parse_value_object(self.value_object, value)
        return parsed.value

    def run_validators(self, value: Any) -> None:
        # CharField's MaxLengthValidator calls len(), so it gets the plain string.
        if isinstance(value, StrValueObject):
            value = value.value
        super().run_validators(value)
