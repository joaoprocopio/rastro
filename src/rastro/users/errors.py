from rastro.base.errors import BaseError


class InvalidEmailError(BaseError):
    code = "AUTH_INVALID_EMAIL"


class InvalidUsernameError(BaseError):
    code = "AUTH_INVALID_USERNAME"


class InvalidNameError(BaseError):
    code = "AUTH_INVALID_NAME"


class InvalidPasswordError(BaseError):
    code = "AUTH_INVALID_PASSWORD"


class EmailAlreadyExistsError(BaseError):
    code = "AUTH_EMAIL_ALREADY_EXISTS"


class UsernameAlreadyExistsError(BaseError):
    code = "AUTH_USERNAME_ALREADY_EXISTS"


class AuthenticationError(BaseError):
    code = "AUTH_AUTHENTICATION_FAILED"
