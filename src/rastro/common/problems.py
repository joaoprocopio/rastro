from __future__ import annotations

from http import HTTPStatus

import pydantic
from django.http import Http404, HttpResponse
from pydantic_core import ErrorDetails

from rastro.common.errors import (
    BaseError,
    FieldRequiredError,
    InvalidFormatError,
    InvalidJsonError,
    InvalidTypeError,
    MethodNotAllowedError,
    NotFoundError,
    TooLongError,
    TooShortError,
    UnknownFieldError,
    ValidationFailedError,
    ValidationItem,
)

PROBLEM_MEDIA_TYPE = "application/problem+json"


def _json_pointer(loc: tuple[int | str, ...]) -> str:
    parts = [str(part).replace("~", "~0").replace("/", "~1") for part in loc]
    return "#" + "".join(f"/{part}" for part in parts)


def _field_error(error: ErrorDetails) -> BaseError:
    ctx = error.get("ctx", {})
    match error["type"]:
        case "missing":
            return FieldRequiredError()
        case "json_invalid":
            return InvalidJsonError()
        case "extra_forbidden":
            return UnknownFieldError()
        # A length rule that runs after a BeforeValidator drops the string_ prefix.
        case "string_too_short" | "too_short":
            return TooShortError(min_length=ctx["min_length"])
        case "string_too_long" | "too_long":
            return TooLongError(max_length=ctx["max_length"])
        case "string_pattern_mismatch":
            return InvalidFormatError()
        case _:
            return InvalidTypeError()


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
    min_length: int | None = None
    max_length: int | None = None

    @classmethod
    def from_item(cls, item: ValidationItem) -> ProblemItem:
        problem_item = cls(pointer=item.pointer, type=_problem_type(item.error.code))
        match item.error:
            case TooShortError():
                problem_item.min_length = item.error.min_length
            case TooLongError():
                problem_item.max_length = item.error.max_length
        return problem_item


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
                problem.errors = [ProblemItem.from_item(item) for item in error.items]
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
