from rastro.base.error import BaseError


class EmailAlreadyExistsError(BaseError):
    code = "USERS_EMAIL_ALREADY_EXISTS"


class UsernameAlreadyExistsError(BaseError):
    code = "USERS_USERNAME_ALREADY_EXISTS"


class AuthenticationError(BaseError):
    code = "USERS_AUTHENTICATION_FAILED"


class UserNotFoundError(BaseError):
    code = "USERS_USER_NOT_FOUND"
