"""RFC 9457 (formerly RFC 7807) problem details, and the handlers that emit them."""

import logging
from collections.abc import Callable, Mapping, Sequence
from http import HTTPStatus

import pydantic
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from rastro.exceptions import BaseError, ErrorCode

log = logging.getLogger(__name__)

PROBLEM_MEDIA_TYPE = "application/problem+json"

# RFC 9457 members that an extension never overwrites. `type` and `instance`
# are reserved by the spec even though the API does not emit them.
RESERVED_MEMBERS = frozenset({"type", "status", "title", "detail", "instance", "code"})


class Problem(pydantic.BaseModel):
    """An RFC 9457 problem details object."""

    model_config = pydantic.ConfigDict(frozen=True)

    code: str
    title: str
    status: int
    detail: str | None = None
    extensions: Mapping[str, object] | None = None

    @pydantic.model_serializer
    def _serialize(self) -> dict[str, object]:
        problem: dict[str, object] = {
            "code": self.code,
            "status": self.status,
            "title": self.title,
        }

        if self.detail is not None:
            problem["detail"] = self.detail

        if self.extensions is not None:
            for key, value in self.extensions.items():
                if key not in RESERVED_MEMBERS:
                    problem[key] = value

        return problem

    @classmethod
    def from_error(cls, error: BaseError) -> Problem:
        return cls(
            code=error.code,
            status=error.status,
            title=error.title,
            detail=error.detail,
            extensions=error.extensions,
        )


class ProblemResponse(JSONResponse):
    media_type = PROBLEM_MEDIA_TYPE


class ValidationIssue(pydantic.BaseModel):
    """One failed constraint of a request.

    The model has no `input` member: pydantic echoes the rejected value there,
    and that value can be a password.
    """

    type: str
    loc: Sequence[str | int]
    msg: str


_VALIDATION_ISSUES = pydantic.TypeAdapter(list[ValidationIssue])


def problem_response(
    problem: Problem, headers: Mapping[str, str] | None = None
) -> ProblemResponse:
    return ProblemResponse(
        problem.model_dump(mode="json"), status_code=problem.status, headers=headers
    )


def handle_base_error(_: Request, exc: BaseError) -> Response:
    return problem_response(Problem.from_error(exc))


def handle_request_validation_error(
    _: Request, exc: RequestValidationError
) -> Response:
    issues = _VALIDATION_ISSUES.validate_python(exc.errors())

    return problem_response(
        Problem(
            code=ErrorCode.BASE_VALIDATION_ERROR,
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
            title="Validation Error",
            detail="The request failed validation.",
            extensions={"errors": [issue.model_dump(mode="json") for issue in issues]},
        )
    )


def handle_http_exception(_: Request, exc: HTTPException) -> Response:
    status = HTTPStatus(exc.status_code)

    return problem_response(
        Problem(
            code=ErrorCode.BASE_HTTP_ERROR,
            status=status,
            title=status.phrase,
            detail=exc.detail if exc.detail != status.phrase else None,
        ),
        headers=exc.headers,
    )


def handle_unexpected_error(_: Request, exc: Exception) -> Response:
    log.exception("Unhandled exception", exc_info=exc)
    status = HTTPStatus.INTERNAL_SERVER_ERROR

    return problem_response(
        Problem(code=ErrorCode.BASE_INTERNAL_ERROR, status=status, title=status.phrase)
    )


def _narrowed[E: Exception](
    exc_type: type[E], handler: Callable[[Request, E], Response]
) -> Callable[[Request, Exception], Response]:
    """Adapt a handler of `exc_type` to the signature Starlette expects.

    Starlette types every handler as taking `Exception`. It only calls the
    handler with an instance of the registered class, and the runtime check
    turns that promise into a type the checker can see.
    """

    def handle(request: Request, exc: Exception) -> Response:
        if not isinstance(exc, exc_type):
            raise exc
        return handler(request, exc)

    return handle


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BaseError, _narrowed(BaseError, handle_base_error))
    app.add_exception_handler(
        RequestValidationError,
        _narrowed(RequestValidationError, handle_request_validation_error),
    )
    app.add_exception_handler(
        HTTPException, _narrowed(HTTPException, handle_http_exception)
    )
    # Starlette sends this response from `ServerErrorMiddleware`, then re-raises
    # the exception so the server still logs it.
    app.add_exception_handler(Exception, handle_unexpected_error)
