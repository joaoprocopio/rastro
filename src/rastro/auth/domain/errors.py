from rastro.common.domain.errors import BaseError


class EmailInUseError(BaseError):
    code = "auth.email_in_use"


class IncorrectCredentialsError(BaseError):
    code = "auth.incorrect_credentials"


class NotAuthenticatedError(BaseError):
    code = "auth.not_authenticated"
