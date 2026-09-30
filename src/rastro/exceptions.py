import enum
from collections.abc import Mapping
from http import HTTPStatus
from typing import ClassVar, Self


@enum.unique
class ErrorCode(enum.StrEnum):
    """The application's catalog of error codes."""

    BASE_VALIDATION_ERROR = "BASE_VALIDATION_ERROR"
    BASE_HTTP_ERROR = "BASE_HTTP_ERROR"
    BASE_INTERNAL_ERROR = "BASE_INTERNAL_ERROR"
    BASE_CSRF_FAILED = "BASE_CSRF_FAILED"
    IAM_INCORRECT_CREDENTIALS = "IAM_INCORRECT_CREDENTIALS"
    IAM_NOT_AUTHENTICATED = "IAM_NOT_AUTHENTICATED"
    IAM_EMAIL_ALREADY_REGISTERED = "IAM_EMAIL_ALREADY_REGISTERED"


_REQUIRED_MEMBERS = ("code", "status", "title")


class BaseError(Exception):
    """Base class for every application error.

    A concrete subclass assigns `code`, `status` and `title`. Instantiating a
    subclass that leaves one of them unassigned raises `TypeError`.
    """

    code: ClassVar[ErrorCode]
    status: ClassVar[HTTPStatus]
    title: ClassVar[str]

    # per-occurrence members, given on instantiation
    detail: str | None
    extensions: Mapping[str, object] | None

    def __new__(
        cls,
        detail: str | None = None,
        *,
        extensions: Mapping[str, object] | None = None,
    ) -> Self:
        missing = [name for name in _REQUIRED_MEMBERS if not hasattr(cls, name)]
        if missing:
            raise TypeError(
                f"Can't instantiate error {cls.__name__} missing: {', '.join(missing)}"
            )
        return super().__new__(cls, detail)

    def __init__(
        self,
        detail: str | None = None,
        *,
        extensions: Mapping[str, object] | None = None,
    ) -> None:
        self.detail = detail
        self.extensions = extensions
        super().__init__(detail)


class CsrfError(BaseError):
    code = ErrorCode.BASE_CSRF_FAILED
    status = HTTPStatus.FORBIDDEN
    title = "CSRF verification failed"
