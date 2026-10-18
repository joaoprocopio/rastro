from http import HTTPStatus

from rastro.common.errors import BaseError


class EmailInUseError(BaseError):
    code = "iam.email_in_use"
    status = HTTPStatus.CONFLICT


class IncorrectCredentialsError(BaseError):
    code = "iam.incorrect_credentials"
    status = HTTPStatus.UNAUTHORIZED


class NotAuthenticatedError(BaseError):
    code = "iam.not_authenticated"
    status = HTTPStatus.UNAUTHORIZED
