from rastro.common.domain.errors import BaseError


class EmailInUseError(BaseError):
    code = "auth.email_in_use"


class IncorrectCredentialsError(BaseError):
    code = "auth.incorrect_credentials"


class NotAuthenticatedError(BaseError):
    code = "auth.not_authenticated"


class InvalidResetTokenError(BaseError):
    code = "auth.invalid_reset_token"


# The email did not go out, and a later attempt may succeed.
class EmailTemporaryError(Exception):
    pass


# The email did not go out, and a later attempt would fail the same way.
class EmailRefusedError(Exception):
    pass


# The email may have gone out.
class EmailNoAnswerError(Exception):
    pass
