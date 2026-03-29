class DomainException(Exception):
    pass


class NotFoundException(DomainException):
    pass


class UnauthorizedException(DomainException):
    pass


class ForbiddenException(DomainException):
    pass


class ConflictException(DomainException):
    pass


class ValidationException(DomainException):
    pass
