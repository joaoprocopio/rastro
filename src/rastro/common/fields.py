from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django import forms
from django.core.exceptions import ValidationError
from django.db import models

from rastro.common.errors import ValidationFailedError
from rastro.common.problems import validation_failed_errors
from rastro.common.values import ValueObject

T = TypeVar("T")
E = TypeVar("E", bound=StrEnum)
V = TypeVar("V", bound=ValueObject[str])


def str_enum_to_choices(str_enum: type[E]) -> list[tuple[str, str]]:
    return [(member.value, member.name) for member in str_enum]


@contextmanager
def django_validation_errors() -> Iterator[None]:
    try:
        with validation_failed_errors():
            yield
    except ValidationFailedError as error:
        raise ValidationError(
            [
                ValidationError(item.error.code, code=item.error.code)
                for item in error.items
            ]
        ) from error


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


class ValueObjectField(_CharField[V]):
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
        return self.value_object.model_validate(value)

    def to_python(self, value: Any) -> V | None:
        if value is None:
            return None
        with django_validation_errors():
            return self.value_object.model_validate(value)

    def get_prep_value(self, value: Any) -> str | None:
        parsed = self.to_python(value)
        return None if parsed is None else parsed.root

    def run_validators(self, value: Any) -> None:
        # CharField's MaxLengthValidator calls len(), so it gets the plain string.
        if isinstance(value, ValueObject):
            value = value.root
        super().run_validators(value)

    def value_from_object(self, obj: models.Model) -> str | None:  # type: ignore[override]
        # The admin form and the serializers read the plain string, not the model repr.
        value = super().value_from_object(obj)
        return value.root if isinstance(value, ValueObject) else value


class ValueObjectFormField(forms.CharField, Generic[V]):
    def __init__(self, value_object: type[V], **kwargs: Any) -> None:
        self.value_object = value_object
        super().__init__(**kwargs)

    def to_python(self, value: Any) -> Any:
        value = super().to_python(value)
        if value in self.empty_values:
            return value
        with django_validation_errors():
            return self.value_object.model_validate(value)
