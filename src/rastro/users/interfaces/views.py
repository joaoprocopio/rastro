from http import HTTPStatus

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from rastro.base.entity import Id
from rastro.users.application.dtos import (
    GetUserInput,
    SignInInput,
    SignUpInput,
)
from rastro.users.application.use_cases import (
    GetUserUseCase,
    SignInUseCase,
    SignUpUseCase,
)
from rastro.users.infrastructure.repository import DjangoUserRepository
from rastro.users.infrastructure.services import (
    DjangoPasswordHashingService,
    DjangoSessionService,
)
from rastro.users.interfaces.presenters import UserPresenter

repository = DjangoUserRepository()
session_service = DjangoSessionService()
password_hashing_service = DjangoPasswordHashingService()

sign_up_use_case = SignUpUseCase(repository)
sign_in_use_case = SignInUseCase(repository, password_hashing_service)
get_user_use_case = GetUserUseCase(repository)


@require_GET  # type: ignore
def me(request: HttpRequest) -> HttpResponse:
    user_id = session_service.access_current_user_id(request)

    if user_id is None:
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    input = GetUserInput(user_id=user_id.value)
    output = get_user_use_case.execute(input)

    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.OK)


@require_POST  # type: ignore
@csrf_exempt  # type: ignore
def sign_up(request: HttpRequest) -> JsonResponse:
    input = SignUpInput.parse_json(request.body)
    output = sign_up_use_case.execute(input)

    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.CREATED)


@require_POST  # type: ignore
@csrf_exempt  # type: ignore
def sign_in(request: HttpRequest) -> JsonResponse:
    input = SignInInput.parse_json(request.body)
    output = sign_in_use_case.execute(input)

    session_service.login(request, Id(output.id))

    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.OK)


def sign_out(request: HttpRequest) -> HttpResponse:
    session_service.logout(request)

    return HttpResponse(status=HTTPStatus.NO_CONTENT)
