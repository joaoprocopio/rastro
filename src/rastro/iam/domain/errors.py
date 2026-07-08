from http import HTTPStatus

from rastro.codes import ErrorCode
from rastro_base.error import BaseError


class IncorrectCredentialsError(BaseError):
    code = ErrorCode.IAM_INCORRECT_CREDENTIALS
    status = HTTPStatus.UNAUTHORIZED
    title = "Incorrect credentials"
