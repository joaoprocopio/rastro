from http import HTTPStatus
from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie

from rastro.conta.application.dtos import CadastrarInput, EntrarInput
from rastro.conta.application.use_cases import (
    CadastrarUseCase,
    ContaUseCase,
    EntrarUseCase,
    SairUseCase,
)
from rastro.conta.infrastructure.composition import (
    django_cadastrar_use_case_factory,
    django_conta_use_case_factory,
    django_entrar_use_case_factory,
    django_sair_use_case_factory,
)
from rastro.conta.shared.mappers import PresentContaMapper


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(View):
    def get(self, _: HttpRequest) -> HttpResponse:
        return HttpResponse(status=HTTPStatus.OK)


class ContaView(View):
    conta_use_case_factory: Callable[[HttpRequest], ContaUseCase] = staticmethod(
        django_conta_use_case_factory
    )

    def get(self, request: HttpRequest) -> HttpResponse:
        conta_use_case = self.conta_use_case_factory(request)
        conta = conta_use_case.execute()

        if conta is None:
            return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

        return JsonResponse(
            PresentContaMapper.map(conta).model_dump(),
            status=HTTPStatus.OK,
        )


class EntrarView(View):
    entrar_use_case_factory: Callable[[HttpRequest], EntrarUseCase] = staticmethod(
        django_entrar_use_case_factory
    )

    def post(self, request: HttpRequest) -> HttpResponse:
        entrar_use_case = self.entrar_use_case_factory(request)
        entrar_input = EntrarInput.model_validate_json(request.body)
        conta_output = entrar_use_case.execute(entrar_input)

        return JsonResponse(
            PresentContaMapper.map(conta_output).model_dump(),
            status=HTTPStatus.OK,
        )


class CadastrarView(View):
    cadastrar_use_case_factory: Callable[[HttpRequest], CadastrarUseCase] = (
        staticmethod(django_cadastrar_use_case_factory)
    )

    def post(self, request: HttpRequest) -> HttpResponse:
        cadastrar_use_case = self.cadastrar_use_case_factory(request)
        input = CadastrarInput.model_validate_json(request.body)
        output = cadastrar_use_case.execute(input)

        return JsonResponse(
            PresentContaMapper.map(output).model_dump(),
            status=HTTPStatus.CREATED,
        )


class SairView(View):
    sair_use_case_factory: Callable[[HttpRequest], SairUseCase] = staticmethod(
        django_sair_use_case_factory
    )

    def post(self, request: HttpRequest) -> HttpResponse:
        sair_use_case = self.sair_use_case_factory(request)
        sair_use_case.execute()

        return HttpResponse(status=HTTPStatus.OK)
