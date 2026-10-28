from __future__ import annotations

from rastro.common.application.dtos import DTO, ExtensibleDTO
from rastro.common.domain.errors import BaseError


class ValidationItem(ExtensibleDTO):
    pointer: str
    type: str

    @classmethod
    def from_error(cls, *, pointer: str, error: BaseError) -> ValidationItem:
        return cls(pointer=pointer, type=error.code, extensions=error.extensions)


class ValidationFailedExtensions(DTO):
    errors: list[ValidationItem]


class ValidationFailedError(BaseError):
    code = "request.validation_failed"

    def __init__(self, extensions: ValidationFailedExtensions) -> None:
        super().__init__(extensions)


class FieldRequiredError(BaseError):
    code = "request.field_required"


class InvalidTypeError(BaseError):
    code = "request.invalid_type"


class InvalidJsonError(BaseError):
    code = "request.invalid_json"


class UnknownFieldError(BaseError):
    code = "request.unknown_field"


class TooShortExtensions(DTO):
    min_length: int


class TooShortError(BaseError):
    code = "request.too_short"

    def __init__(self, extensions: TooShortExtensions) -> None:
        super().__init__(extensions)


class TooLongExtensions(DTO):
    max_length: int


class TooLongError(BaseError):
    code = "request.too_long"

    def __init__(self, extensions: TooLongExtensions) -> None:
        super().__init__(extensions)


class InvalidFormatError(BaseError):
    code = "request.invalid_format"


class NotFoundError(BaseError):
    code = "request.not_found"


class MethodNotAllowedError(BaseError):
    code = "request.method_not_allowed"


class InternalServerError(BaseError):
    code = "server.internal_error"
