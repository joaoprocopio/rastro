from collections.abc import Callable
from functools import wraps
from http import HTTPStatus
from typing import Concatenate, ParamSpec, TypeVar

import pydantic
from django.http import HttpRequest, HttpResponse

from rastro.common.errors import RequestCode
from rastro.common.middleware import STATUS_BY_CODE
from rastro.common.problems import problem_response

Schema = TypeVar("Schema", bound=pydantic.BaseModel)
P = ParamSpec("P")
View = Callable[Concatenate[HttpRequest, P], HttpResponse]


def parse_body(request: HttpRequest, schema: type[Schema]) -> Schema:
    return schema.model_validate_json(request.body)


def respond(
    *, status: HTTPStatus, output: pydantic.BaseModel | None = None
) -> HttpResponse:
    if output is None:
        return HttpResponse(status=status)
    return HttpResponse(
        output.model_dump_json(), status=status, content_type="application/json"
    )


def _require_method(method: str, view: View[P]) -> View[P]:
    @wraps(view)
    def guarded(
        request: HttpRequest, /, *args: P.args, **kwargs: P.kwargs
    ) -> HttpResponse:
        if request.method != method:
            response = problem_response(HTTPStatus.METHOD_NOT_ALLOWED)
            response["Allow"] = method
            return response
        return view(request, *args, **kwargs)

    return guarded


def require_POST(view: View[P]) -> View[P]:
    return _require_method("POST", view)


def require_GET(view: View[P]) -> View[P]:
    return _require_method("GET", view)


def csrf_failure_view(request: HttpRequest, reason: str = "") -> HttpResponse:
    return problem_response(
        STATUS_BY_CODE[RequestCode.CSRF_FAILED], code=RequestCode.CSRF_FAILED
    )


def not_found_view(request: HttpRequest, exception: Exception) -> HttpResponse:
    return problem_response(HTTPStatus.NOT_FOUND)


def server_error_view(request: HttpRequest) -> HttpResponse:
    return problem_response(HTTPStatus.INTERNAL_SERVER_ERROR)
