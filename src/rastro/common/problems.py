from http import HTTPStatus

from django.http import JsonResponse

PROBLEM_MEDIA_TYPE = "application/problem+json"


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
