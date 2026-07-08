import pydantic
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from rastro_base.error import BaseError
from rastro_base.problem import (
    Problem,
    ProblemMapper,
    ValidationErrorMapper,
)


class ExceptionHandlerMiddleware(MiddlewareMixin):
    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> HttpResponse | None:
        problem: Problem

        match exception:
            case BaseError():
                problem = ProblemMapper.map(exception)
            case pydantic.ValidationError():
                problem = ValidationErrorMapper.map(exception)
            case _:
                return None

        return JsonResponse(
            problem.model_dump(),
            status=problem.status,
            content_type="application/problem+json",
        )
