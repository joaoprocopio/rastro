from http import HTTPStatus

from rastro.exceptions import BaseError, ErrorCode


class IncorrectCredentialsError(BaseError):
    code = ErrorCode.IAM_INCORRECT_CREDENTIALS
    status = HTTPStatus.UNAUTHORIZED
    title = "Incorrect credentials"


class NotAuthenticatedError(BaseError):
    code = ErrorCode.IAM_NOT_AUTHENTICATED
    status = HTTPStatus.UNAUTHORIZED
    title = "Not authenticated"


class EmailAlreadyRegisteredError(BaseError):
    code = ErrorCode.IAM_EMAIL_ALREADY_REGISTERED
    status = HTTPStatus.CONFLICT
    title = "Email already registered"
