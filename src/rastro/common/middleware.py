from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from rastro.common.problems import Problem, problem_response, to_error


class ProblemDetailsMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> HttpResponse | None:
        error = to_error(exception)
        if error is None:
            return None
        return problem_response(Problem.from_error(error))
