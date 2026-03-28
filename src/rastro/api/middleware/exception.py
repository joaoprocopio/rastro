from typing import Callable
from http import HTTPStatus

from django.http import HttpRequest, HttpResponse
from django.conf import settings

from rastro.shared.domain.exceptions import (
    DomainException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    ValidationException,
)
from rastro.api.common.responses import error_response


class ExceptionMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> HttpResponse | None:
        if isinstance(exception, NotFoundException):
            return error_response(
                str(exception),
                code="NOT_FOUND",
                status=HTTPStatus.NOT_FOUND,
            )

        if isinstance(exception, UnauthorizedException):
            return error_response(
                str(exception),
                code="UNAUTHORIZED",
                status=HTTPStatus.UNAUTHORIZED,
            )

        if isinstance(exception, ForbiddenException):
            return error_response(
                str(exception),
                code="FORBIDDEN",
                status=HTTPStatus.FORBIDDEN,
            )

        if isinstance(exception, ConflictException):
            return error_response(
                str(exception),
                code="CONFLICT",
                status=HTTPStatus.CONFLICT,
            )

        if isinstance(exception, ValidationException):
            return error_response(
                str(exception),
                code="VALIDATION_ERROR",
                status=HTTPStatus.BAD_REQUEST,
            )

        if isinstance(exception, DomainException):
            return error_response(
                str(exception),
                code="DOMAIN_ERROR",
                status=HTTPStatus.BAD_REQUEST,
            )

        if settings.DEBUG:
            return None

        return error_response(
            "Internal server error",
            code="INTERNAL_ERROR",
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
