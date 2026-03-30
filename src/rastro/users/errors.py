from rastro.base.errors import BaseError


class InvalidEmailError(BaseError):
    code = "USERS_INVALID_EMAIL"


class InvalidUsernameError(BaseError):
    code = "USERS_INVALID_USERNAME"


class InvalidNameError(BaseError):
    code = "USERS_INVALID_NAME"


class InvalidPasswordError(BaseError):
    code = "USERS_INVALID_PASSWORD"


class EmailAlreadyExistsError(BaseError):
    code = "USERS_EMAIL_ALREADY_EXISTS"


class UsernameAlreadyExistsError(BaseError):
    code = "USERS_USERNAME_ALREADY_EXISTS"


class AuthenticationError(BaseError):
    code = "USERS_AUTHENTICATION_FAILED"
