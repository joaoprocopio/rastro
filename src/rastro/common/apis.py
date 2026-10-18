from collections.abc import Callable
from functools import wraps
from http import HTTPStatus
from typing import Concatenate, ParamSpec, TypeVar

import pydantic
from django.http import HttpRequest, HttpResponse, JsonResponse

PROBLEM_MEDIA_TYPE = "application/problem+json"

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


def problem_type(code: str) -> str:
    return f"/problems/{code}"


def problem_response(
    status: HTTPStatus,
    *,
    code: str | None = None,
    errors: list[dict[str, str]] | None = None,
) -> JsonResponse:
    problem: dict[str, object] = {}
    if code is not None:
        problem["type"] = problem_type(code)
    problem["status"] = int(status)
    if errors is not None:
        problem["errors"] = errors
    return JsonResponse(problem, status=status, content_type=PROBLEM_MEDIA_TYPE)


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
