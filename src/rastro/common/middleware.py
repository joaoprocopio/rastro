from collections.abc import Callable
from http import HTTPStatus

import pydantic
from django.http import HttpRequest, HttpResponse
from pydantic_core import ErrorDetails

from rastro.common.errors import ApplicationError, RequestCode
from rastro.common.problems import problem_response, problem_type
from rastro.common.values import InvalidValueError

STATUS_BY_CODE: dict[str, HTTPStatus] = {
    RequestCode.VALIDATION_FAILED: HTTPStatus.UNPROCESSABLE_ENTITY,
    RequestCode.CSRF_FAILED: HTTPStatus.FORBIDDEN,
    "iam.email_in_use": HTTPStatus.CONFLICT,
    "iam.incorrect_credentials": HTTPStatus.UNAUTHORIZED,
    "iam.not_authenticated": HTTPStatus.UNAUTHORIZED,
}

# Any other Pydantic error, for example string_type or int_parsing, is a wrong type.
_REQUEST_CODE_BY_PYDANTIC_TYPE: dict[str, RequestCode] = {
    "missing": RequestCode.FIELD_REQUIRED,
    "json_invalid": RequestCode.INVALID_JSON,
    "extra_forbidden": RequestCode.UNKNOWN_FIELD,
}


def _json_pointer(loc: tuple[int | str, ...]) -> str:
    parts = [str(part).replace("~", "~0").replace("/", "~1") for part in loc]
    return "#" + "".join(f"/{part}" for part in parts)


def _item_code(error: ErrorDetails) -> str:
    cause = error.get("ctx", {}).get("error")
    if isinstance(cause, InvalidValueError):
        return cause.code
    return _REQUEST_CODE_BY_PYDANTIC_TYPE.get(error["type"], RequestCode.INVALID_TYPE)


def _validation_failed_response(exception: pydantic.ValidationError) -> HttpResponse:
    errors = [
        {
            "pointer": _json_pointer(error["loc"]),
            "type": problem_type(_item_code(error)),
        }
        for error in exception.errors(include_url=False, include_input=False)
    ]
    return problem_response(
        STATUS_BY_CODE[RequestCode.VALIDATION_FAILED],
        code=RequestCode.VALIDATION_FAILED,
        errors=errors,
    )


class ProblemDetailsMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> HttpResponse | None:
        match exception:
            case ApplicationError():
                return problem_response(
                    STATUS_BY_CODE[exception.code], code=exception.code
                )
            case pydantic.ValidationError():
                return _validation_failed_response(exception)
            case _:
                return None
