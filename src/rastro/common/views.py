from http import HTTPStatus

from django.http import HttpRequest, HttpResponse

from rastro.common.apis import problem_response
from rastro.common.errors import RequestCode
from rastro.common.middleware import STATUS_BY_CODE


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    return problem_response(
        STATUS_BY_CODE[RequestCode.CSRF_FAILED], code=RequestCode.CSRF_FAILED
    )


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return problem_response(HTTPStatus.NOT_FOUND)


def server_error(request: HttpRequest) -> HttpResponse:
    return problem_response(HTTPStatus.INTERNAL_SERVER_ERROR)
