from rastro.common.errors import ApplicationError


class EmailInUseError(ApplicationError):
    code = "iam.email_in_use"


class IncorrectCredentialsError(ApplicationError):
    code = "iam.incorrect_credentials"


class NotAuthenticatedError(ApplicationError):
    code = "iam.not_authenticated"
