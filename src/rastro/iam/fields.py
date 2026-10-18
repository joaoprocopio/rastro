from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.core.exceptions import ValidationError
from django.db import models

from rastro.common.values import InvalidValueError, StrValueObject
from rastro.iam.values import DisplayName, Email

V = TypeVar("V", bound=StrValueObject)


if TYPE_CHECKING:
    _CharField = models.CharField[V, V]
else:
    # Django's Field has no __class_getitem__, so the runtime base adds one through Generic.
    class _CharField(models.CharField, Generic[V]):
        pass


class StrValueObjectField(_CharField[V]):
    value_object: type[V]

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> V | None:
        if value is None:
            return None
        return self.value_object(value)

    def to_python(self, value: Any) -> V | None:
        if value is None or isinstance(value, self.value_object):
            return value
        try:
            return self.value_object(value)
        except InvalidValueError as error:
            raise ValidationError(str(error), code=error.code) from error

    def get_prep_value(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, StrValueObject):
            return value.value
        return self.value_object(value).value

    def run_validators(self, value: Any) -> None:
        # CharField's MaxLengthValidator calls len(), so it gets the plain string.
        if isinstance(value, StrValueObject):
            value = value.value
        super().run_validators(value)

    def value_to_string(self, obj: models.Model) -> str:
        value = self.value_from_object(obj)
        return value.value if isinstance(value, StrValueObject) else str(value)


class EmailField(StrValueObjectField[Email]):
    value_object = Email

    # The django-stubs plugin reads these to type the model's __init__ arguments.
    if TYPE_CHECKING:
        _pyi_private_set_type: Email  # type: ignore[assignment]
        _pyi_private_get_type: Email  # type: ignore[assignment]


class DisplayNameField(StrValueObjectField[DisplayName]):
    value_object = DisplayName

    if TYPE_CHECKING:
        _pyi_private_set_type: DisplayName  # type: ignore[assignment]
        _pyi_private_get_type: DisplayName  # type: ignore[assignment]
