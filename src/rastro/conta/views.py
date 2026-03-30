from http import HTTPStatus

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.views.decorators.http import require_GET

from rastro.conta.repository import DjangoContaRepository
from rastro.conta.use_cases import CadastrarUseCase, EntrarUseCase

repository = DjangoContaRepository()
entrar_use_case = EntrarUseCase(repository)
cadastrar_use_case = CadastrarUseCase(repository)


@require_GET  # type: ignore[misc]
def conta(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    return HttpResponse()
