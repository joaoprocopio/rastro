from rastro.base.error import BaseError


class AuthenticationError(BaseError):
    code = "AUTH_AUTHENTICATION_FAILED"


class UserNotFoundError(BaseError):
    code = "AUTH_USER_NOT_FOUND"
