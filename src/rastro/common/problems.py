from __future__ import annotations

from http import HTTPStatus

import pydantic
from django.http import Http404, HttpResponse
from pydantic_core import ErrorDetails

from rastro.common.errors import (
    BaseError,
    FieldRequiredError,
    InvalidJsonError,
    InvalidTypeError,
    MethodNotAllowedError,
    NotFoundError,
    UnknownFieldError,
    ValidationFailedError,
    ValidationItem,
)
from rastro.common.values import InvalidValueError

PROBLEM_MEDIA_TYPE = "application/problem+json"

# Any other Pydantic error type, for example string_type or int_parsing, is a wrong type.
_FIELD_ERROR_BY_PYDANTIC_TYPE: dict[str, type[BaseError]] = {
    "missing": FieldRequiredError,
    "json_invalid": InvalidJsonError,
    "extra_forbidden": UnknownFieldError,
}


def _json_pointer(loc: tuple[int | str, ...]) -> str:
    parts = [str(part).replace("~", "~0").replace("/", "~1") for part in loc]
    return "#" + "".join(f"/{part}" for part in parts)


def _field_error(error: ErrorDetails) -> BaseError | InvalidValueError:
    cause = error.get("ctx", {}).get("error")
    if isinstance(cause, InvalidValueError):
        return cause
    return _FIELD_ERROR_BY_PYDANTIC_TYPE.get(error["type"], InvalidTypeError)()


def to_error(exception: Exception) -> BaseError | None:
    match exception:
        case BaseError():
            return exception
        case pydantic.ValidationError():
            return ValidationFailedError(
                [
                    ValidationItem(
                        pointer=_json_pointer(error["loc"]), error=_field_error(error)
                    )
                    for error in exception.errors(
                        include_url=False, include_input=False
                    )
                ]
            )
        case Http404():
            return NotFoundError()
        case _:
            return None


def _problem_type(code: str) -> str:
    return f"/problems/{code}"


class ProblemItem(pydantic.BaseModel):
    pointer: str
    type: str


class Problem(pydantic.BaseModel):
    type: str
    status: HTTPStatus
    errors: list[ProblemItem] | None = None
    # A header of the response, never a member of the body.
    allow: str | None = pydantic.Field(default=None, exclude=True)

    @classmethod
    def from_error(cls, error: BaseError) -> Problem:
        problem = cls(type=_problem_type(error.code), status=error.status)
        match error:
            case ValidationFailedError():
                problem.errors = [
                    ProblemItem(
                        pointer=item.pointer, type=_problem_type(item.error.code)
                    )
                    for item in error.items
                ]
            case MethodNotAllowedError():
                problem.allow = error.allow
        return problem


def problem_response(problem: Problem) -> HttpResponse:
    response = HttpResponse(
        problem.model_dump_json(exclude_none=True),
        status=problem.status,
        content_type=PROBLEM_MEDIA_TYPE,
    )
    if problem.allow is not None:
        response["Allow"] = problem.allow
    return response
