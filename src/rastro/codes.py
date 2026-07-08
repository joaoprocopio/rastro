import enum


@enum.unique
class ErrorCode(enum.StrEnum):
    """The application's catalog of error codes."""

    BASE_VALIDATION_ERROR = "BASE_VALIDATION_ERROR"
    IAM_INCORRECT_CREDENTIALS = "IAM_INCORRECT_CREDENTIALS"
