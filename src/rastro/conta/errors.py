from rastro.base.errors import BaseError


class InvalidEmailError(BaseError):
    code = "INVALID_EMAIL"


class InvalidUsernameError(BaseError):
    code = "INVALID_USERNAME"


class InvalidNameError(BaseError):
    code = "INVALID_NAME"


class InvalidPasswordError(BaseError):
    code = "INVALID_PASSWORD"


class EmailAlreadyExistsError(BaseError):
    code = "EMAIL_ALREADY_EXISTS"


class UsernameAlreadyExistsError(BaseError):
    code = "USERNAME_ALREADY_EXISTS"


class AuthenticationError(BaseError):
    code = "AUTHENTICATION_FAILED"
