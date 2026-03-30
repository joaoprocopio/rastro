from http import HTTPStatus

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from rastro.auth.application.dtos import (
    SignInInput,
    SignUpInput,
)
from rastro.auth.application.use_cases import (
    SignInUseCase,
    SignUpUseCase,
)
from rastro.auth.infrastructure.mappers import (
    DomainToOutputUserMapper,
    OutputToDomainUserMapper,
)
from rastro.auth.infrastructure.repository import DjangoUserRepository
from rastro.auth.infrastructure.services import (
    DjangoPasswordHashingService,
    DjangoSessionService,
)
from rastro.auth.interfaces.presenters import UserPresenter


@require_GET  # type: ignore
def me(request: HttpRequest) -> HttpResponse:
    session_service = DjangoSessionService(request)

    user = session_service.logged_user()

    if user is None:
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    return JsonResponse(
        UserPresenter.present(DomainToOutputUserMapper.map(user)), status=HTTPStatus.OK
    )


@require_POST  # type: ignore
@csrf_exempt  # type: ignore
def sign_in(request: HttpRequest) -> JsonResponse:
    repository = DjangoUserRepository()
    password_hashing_service = DjangoPasswordHashingService()
    sign_in_use_case = SignInUseCase(repository, password_hashing_service)
    session_service = DjangoSessionService(request)

    input = SignInInput.parse_json(request.body)
    output = sign_in_use_case.execute(input)

    session_service.login(OutputToDomainUserMapper.map(output))

    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.OK)


@require_POST  # type: ignore
@csrf_exempt  # type: ignore
def sign_up(request: HttpRequest) -> JsonResponse:
    repository = DjangoUserRepository()
    password_hashing_service = DjangoPasswordHashingService()
    sign_up_use_case = SignUpUseCase(repository, password_hashing_service)

    input = SignUpInput.parse_json(request.body)
    output = sign_up_use_case.execute(input)

    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.CREATED)


@require_POST  # type: ignore
def sign_out(request: HttpRequest) -> HttpResponse:
    session_service = DjangoSessionService(request)

    session_service.logout()

    return HttpResponse(status=HTTPStatus.NO_CONTENT)
