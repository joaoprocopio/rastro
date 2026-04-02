# views.py
from http import HTTPStatus

from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from rastro.auth.application.dtos import SignInInput, SignUpInput
from rastro.auth.application.use_cases import SignInUseCase, SignUpUseCase
from rastro.auth.infrastructure.mappers import (
    DomainToPublicUserMapper,
    OutputToDomainUserMapper,
    OutputToPublicUserMapper,
)
from rastro.auth.infrastructure.repositories import DjangoUserRepository
from rastro.auth.infrastructure.services import (
    DjangoPasswordHashingService,
    DjangoSessionService,
)
from rastro_shared_kernel.constants import CONTENT_TYPE_JSON


@method_decorator(ensure_csrf_cookie, name="get")
class MeView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        session_service = DjangoSessionService(request)
        user = session_service.logged_user()

        if user is None:
            return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

        return HttpResponse(
            DomainToPublicUserMapper.map(user).model_dump_json(),
            status=HTTPStatus.OK,
            content_type=CONTENT_TYPE_JSON,
        )


@method_decorator(csrf_exempt, name="dispatch")
class SignInView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        repository = DjangoUserRepository()
        password_hashing_service = DjangoPasswordHashingService()
        sign_in_use_case = SignInUseCase(repository, password_hashing_service)
        session_service = DjangoSessionService(request)

        input = SignInInput.model_validate_json(request.body)
        output = sign_in_use_case.execute(input)

        session_service.login(OutputToDomainUserMapper.map(output))

        return HttpResponse(
            OutputToPublicUserMapper.map(output).model_dump_json(),
            status=HTTPStatus.OK,
            content_type=CONTENT_TYPE_JSON,
        )


@method_decorator(csrf_exempt, name="dispatch")
class SignUpView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        repository = DjangoUserRepository()
        password_hashing_service = DjangoPasswordHashingService()
        sign_up_use_case = SignUpUseCase(repository, password_hashing_service)
        session_service = DjangoSessionService(request)

        input = SignUpInput.model_validate_json(request.body)
        output = sign_up_use_case.execute(input)

        session_service.login(OutputToDomainUserMapper.map(output))

        return HttpResponse(
            OutputToPublicUserMapper.map(output).model_dump_json(),
            status=HTTPStatus.CREATED,
            content_type=CONTENT_TYPE_JSON,
        )


class SignOutView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        session_service = DjangoSessionService(request)
        user = session_service.logged_user()

        if user is None:
            return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

        session_service.logout()

        return HttpResponse(status=HTTPStatus.NO_CONTENT)
