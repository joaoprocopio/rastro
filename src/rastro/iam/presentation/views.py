from http import HTTPStatus
from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie

from rastro.iam.application.dtos import AuthenticateInputDTO, RegisterIdentityInputDTO
from rastro.iam.application.use_cases import (
    AuthenticateUseCase,
    EndSessionUseCase,
    GetCurrentIdentityUseCase,
    RegisterIdentityUseCase,
)
from rastro.iam.infrastructure.composition import (
    django_authenticate_use_case_factory,
    django_end_session_use_case_factory,
    django_get_current_identity_use_case_factory,
    django_register_identity_use_case_factory,
)
from rastro.iam.shared.mappers import PresentIdentityMapper


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(View):
    def get(self, _: HttpRequest) -> HttpResponse:
        return HttpResponse(status=HTTPStatus.OK)


class IdentitiesView(View):
    register_identity_use_case_factory: Callable[
        [HttpRequest], RegisterIdentityUseCase
    ] = staticmethod(django_register_identity_use_case_factory)

    def post(self, request: HttpRequest) -> HttpResponse:
        register_identity_use_case = self.register_identity_use_case_factory(request)
        input = RegisterIdentityInputDTO.model_validate_json(request.body)
        output = register_identity_use_case.execute(input)

        return JsonResponse(
            PresentIdentityMapper.map(output).model_dump(),
            status=HTTPStatus.CREATED,
        )


class SessionView(View):
    authenticate_use_case_factory: Callable[
        [HttpRequest], AuthenticateUseCase
    ] = staticmethod(django_authenticate_use_case_factory)
    end_session_use_case_factory: Callable[
        [HttpRequest], EndSessionUseCase
    ] = staticmethod(django_end_session_use_case_factory)
    get_current_identity_use_case_factory: Callable[
        [HttpRequest], GetCurrentIdentityUseCase
    ] = staticmethod(django_get_current_identity_use_case_factory)

    def post(self, request: HttpRequest) -> HttpResponse:
        authenticate_use_case = self.authenticate_use_case_factory(request)
        input = AuthenticateInputDTO.model_validate_json(request.body)
        output = authenticate_use_case.execute(input)

        return JsonResponse(
            PresentIdentityMapper.map(output).model_dump(),
            status=HTTPStatus.OK,
        )

    def get(self, request: HttpRequest) -> HttpResponse:
        get_current_identity_use_case = self.get_current_identity_use_case_factory(
            request
        )
        identity = get_current_identity_use_case.execute()

        if identity is None:
            return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

        return JsonResponse(
            PresentIdentityMapper.map(identity).model_dump(),
            status=HTTPStatus.OK,
        )

    def delete(self, request: HttpRequest) -> HttpResponse:
        end_session_use_case = self.end_session_use_case_factory(request)
        end_session_use_case.execute()

        return HttpResponse(status=HTTPStatus.NO_CONTENT)
