from http import HTTPStatus

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.views.decorators.http import require_GET

from rastro.conta.dto import ContaOutput


@require_GET  # type: ignore[misc]
def conta(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    conta = ContaOutput

    return HttpResponse()
