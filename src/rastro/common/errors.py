from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import ClassVar

from rastro.common.values import InvalidValueError


def _name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


class BaseError(Exception):
    code: ClassVar[str]
    status: ClassVar[HTTPStatus]

    _class_by_code: ClassVar[dict[str, type[BaseError]]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "code" not in cls.__dict__:
            raise TypeError(f"{_name(cls)} declares no code.")
        if "status" not in cls.__dict__:
            raise TypeError(f"{_name(cls)} declares no status.")
        owner = BaseError._class_by_code.setdefault(cls.code, cls)
        if owner is not cls:
            raise TypeError(
                f"{_name(cls)} declares the code {cls.code!r}, "
                f"which {_name(owner)} already declares."
            )

    def __init__(self) -> None:
        super().__init__(self.code)


@dataclass(frozen=True)
class ValidationItem:
    pointer: str
    # A value object still raises InvalidValueError, which carries a code of its own.
    error: BaseError | InvalidValueError


class ValidationFailedError(BaseError):
    code = "request.validation_failed"
    status = HTTPStatus.UNPROCESSABLE_ENTITY

    def __init__(self, items: list[ValidationItem]) -> None:
        super().__init__()
        self.items = items


class FieldRequiredError(BaseError):
    code = "request.field_required"
    status = HTTPStatus.UNPROCESSABLE_ENTITY


class InvalidTypeError(BaseError):
    code = "request.invalid_type"
    status = HTTPStatus.UNPROCESSABLE_ENTITY


class InvalidJsonError(BaseError):
    code = "request.invalid_json"
    status = HTTPStatus.UNPROCESSABLE_ENTITY


class UnknownFieldError(BaseError):
    code = "request.unknown_field"
    status = HTTPStatus.UNPROCESSABLE_ENTITY


class TooShortError(BaseError):
    code = "request.too_short"
    status = HTTPStatus.UNPROCESSABLE_ENTITY


class TooLongError(BaseError):
    code = "request.too_long"
    status = HTTPStatus.UNPROCESSABLE_ENTITY


class InvalidFormatError(BaseError):
    code = "request.invalid_format"
    status = HTTPStatus.UNPROCESSABLE_ENTITY


class CsrfFailedError(BaseError):
    code = "request.csrf_failed"
    status = HTTPStatus.FORBIDDEN


class NotFoundError(BaseError):
    code = "request.not_found"
    status = HTTPStatus.NOT_FOUND


class MethodNotAllowedError(BaseError):
    code = "request.method_not_allowed"
    status = HTTPStatus.METHOD_NOT_ALLOWED

    def __init__(self, allow: str) -> None:
        super().__init__()
        self.allow = allow


class InternalServerError(BaseError):
    code = "server.internal_error"
    status = HTTPStatus.INTERNAL_SERVER_ERROR
