from enum import StrEnum
from typing import ClassVar


class ApplicationError(Exception):
    code: ClassVar[str]

    def __init_subclass__(cls) -> None:
        if "code" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} declares no code.")

    def __init__(self) -> None:
        super().__init__(self.code)


class RequestCode(StrEnum):
    VALIDATION_FAILED = "request.validation_failed"
    FIELD_REQUIRED = "request.field_required"
    INVALID_TYPE = "request.invalid_type"
    INVALID_JSON = "request.invalid_json"
    UNKNOWN_FIELD = "request.unknown_field"
    CSRF_FAILED = "request.csrf_failed"
