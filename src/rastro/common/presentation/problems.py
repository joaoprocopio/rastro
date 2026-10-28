from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from functools import partial
from http import HTTPStatus

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic_core import ErrorDetails
from starlette.exceptions import HTTPException

from rastro.common.application.dtos import ExtensibleDTO
from rastro.common.domain.errors import BaseError
from rastro.common.presentation.errors import (
    CsrfFailedError,
    FieldRequiredError,
    InternalServerError,
    InvalidFormatError,
    InvalidJsonError,
    InvalidTypeError,
    MethodNotAllowedError,
    NotFoundError,
    TooLongError,
    TooLongExtensions,
    TooShortError,
    TooShortExtensions,
    UnknownFieldError,
    ValidationFailedError,
    ValidationFailedExtensions,
    ValidationItem,
)

PROBLEM_MEDIA_TYPE = "application/problem+json"

type ErrorStatuses = Mapping[type[BaseError], HTTPStatus]

ERROR_STATUSES: ErrorStatuses = {
    ValidationFailedError: HTTPStatus.UNPROCESSABLE_ENTITY,
    FieldRequiredError: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidTypeError: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidJsonError: HTTPStatus.UNPROCESSABLE_ENTITY,
    UnknownFieldError: HTTPStatus.UNPROCESSABLE_ENTITY,
    TooShortError: HTTPStatus.UNPROCESSABLE_ENTITY,
    TooLongError: HTTPStatus.UNPROCESSABLE_ENTITY,
    InvalidFormatError: HTTPStatus.UNPROCESSABLE_ENTITY,
    CsrfFailedError: HTTPStatus.FORBIDDEN,
    NotFoundError: HTTPStatus.NOT_FOUND,
    MethodNotAllowedError: HTTPStatus.METHOD_NOT_ALLOWED,
    InternalServerError: HTTPStatus.INTERNAL_SERVER_ERROR,
}


class Problem(ExtensibleDTO):
    type: str
    status: HTTPStatus
    title: str | None = None
    detail: str | None = None
    instance: str | None = None

    @classmethod
    def from_error(cls, error: BaseError, *, status: HTTPStatus) -> Problem:
        return cls(type=error.code, status=status, extensions=error.extensions)


def _problem_response(
    error: BaseError,
    *,
    error_statuses: ErrorStatuses,
    headers: Mapping[str, str] | None = None,
) -> Response:
    # An error without a row raises, and the next handler answers 500.
    problem = Problem.from_error(error, status=error_statuses[type(error)])
    return JSONResponse(
        problem.model_dump(mode="json"),
        status_code=problem.status,
        headers=headers,
        media_type=PROBLEM_MEDIA_TYPE,
    )


async def _answer_base_error(
    error_statuses: ErrorStatuses, request: Request, exception: Exception
) -> Response:
    if not isinstance(exception, BaseError):
        raise exception
    return _problem_response(exception, error_statuses=error_statuses)


def _body_pointer(loc: tuple[int | str, ...]) -> str:
    source, *path = loc
    if source != "body":
        raise ValueError(f"No JSON Pointer for a {source!r} parameter.")
    parts = [str(part).replace("~", "~0").replace("/", "~1") for part in path]
    return "#" + "".join(f"/{part}" for part in parts)


def _field_error(error: ErrorDetails) -> BaseError:
    match error["type"]:
        case "json_invalid":
            return InvalidJsonError()
        case "missing":
            return FieldRequiredError()
        case "extra_forbidden":
            return UnknownFieldError()
        # from_attributes turns the model_type of a body that is no object into this.
        case "string_type" | "int_type" | "model_attributes_type":
            return InvalidTypeError()
        # A length rule that runs after a BeforeValidator drops the string_ prefix.
        case "string_too_short" | "too_short":
            return TooShortError(
                TooShortExtensions(min_length=error["ctx"]["min_length"])
            )
        case "string_too_long" | "too_long":
            return TooLongError(
                TooLongExtensions(max_length=error["ctx"]["max_length"])
            )
        case "string_pattern_mismatch":
            return InvalidFormatError()
        case _:
            raise LookupError(
                f"No problem for the Pydantic error type {error['type']!r}."
            )


def _validation_item(error: ErrorDetails) -> ValidationItem:
    field_error = _field_error(error)
    # FastAPI puts the character offset of a JSON syntax error in loc.
    pointer = (
        "#"
        if isinstance(field_error, InvalidJsonError)
        else _body_pointer(error["loc"])
    )
    return ValidationItem.from_error(pointer=pointer, error=field_error)


async def _answer_request_validation_error(
    error_statuses: ErrorStatuses, request: Request, exception: Exception
) -> Response:
    if not isinstance(exception, RequestValidationError):
        raise exception
    items = [_validation_item(error) for error in exception.errors()]
    return _problem_response(
        ValidationFailedError(ValidationFailedExtensions(errors=items)),
        error_statuses=error_statuses,
    )


async def _answer_http_exception(
    error_statuses: ErrorStatuses, request: Request, exception: Exception
) -> Response:
    if not isinstance(exception, HTTPException):
        raise exception
    match exception.status_code:
        case HTTPStatus.NOT_FOUND:
            return _problem_response(NotFoundError(), error_statuses=error_statuses)
        case HTTPStatus.METHOD_NOT_ALLOWED:
            # Starlette's router puts the allowed methods of the route in this header.
            headers = exception.headers
            if headers is None:
                raise exception
            return _problem_response(
                MethodNotAllowedError(),
                error_statuses=error_statuses,
                headers={"Allow": headers["Allow"]},
            )
        case _:
            raise exception


async def _answer_internal_error(
    error_statuses: ErrorStatuses, request: Request, exception: Exception
) -> Response:
    # Starlette sends this response, then raises the exception again for the server log.
    return _problem_response(InternalServerError(), error_statuses=error_statuses)


_HANDLERS: dict[
    type[Exception],
    Callable[[ErrorStatuses, Request, Exception], Awaitable[Response]],
] = {
    RequestValidationError: _answer_request_validation_error,
    BaseError: _answer_base_error,
    HTTPException: _answer_http_exception,
    Exception: _answer_internal_error,
}


def install_problem_handlers(app: FastAPI, *, error_statuses: ErrorStatuses) -> None:
    for exception_class, handler in _HANDLERS.items():
        app.add_exception_handler(exception_class, partial(handler, error_statuses))
