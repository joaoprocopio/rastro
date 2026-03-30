import json
from http import HTTPStatus

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from rastro.base.entity import Id
from rastro.users.application.dtos import (
    GetUserInput,
    ResetPasswordInput,
    SignInInput,
    SignUpInput,
    UserOutput,
    VerifyEmailInput,
)
from rastro.users.application.use_cases import (
    GetUserUseCase,
    RequestPasswordResetUseCase,
    ResetPasswordUseCase,
    SignInUseCase,
    SignUpUseCase,
    VerifyEmailUseCase,
)
from rastro.users.infrastructure.repository import DjangoUserRepository
from rastro.users.infrastructure.services import (
    DjangoPasswordHashingService,
    DjangoSessionService,
    DjangoTokenService,
)
from rastro.users.interfaces.presenters import UserPresenter

repository = DjangoUserRepository()
password_hashing_service = DjangoPasswordHashingService()
session_service = DjangoSessionService()
token_service = DjangoTokenService()

sign_up_use_case = SignUpUseCase(repository, password_hashing_service)
sign_in_use_case = SignInUseCase(repository, password_hashing_service)
get_user_use_case = GetUserUseCase(repository)
request_password_reset_use_case = RequestPasswordResetUseCase(repository, token_service)
reset_password_use_case = ResetPasswordUseCase(
    repository, token_service, password_hashing_service
)
verify_email_use_case = VerifyEmailUseCase(repository, token_service)


@require_POST  # type: ignore[misc]
@csrf_exempt  # type: ignore[misc]
def sign_up(request: HttpRequest) -> JsonResponse:
    input = SignUpInput.from_str(request.body)
    output = sign_up_use_case.execute(input)

    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.CREATED)


@require_POST  # type: ignore[misc]
@csrf_exempt  # type: ignore[misc]
def sign_in(request: HttpRequest) -> JsonResponse:
    input = SignInInput.from_str(request.body)
    output = sign_in_use_case.execute(input)

    session_service.login(request, Id(output.id))

    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.OK)


def sign_out(request: HttpRequest) -> HttpResponse:
    session_service.logout(request)

    return HttpResponse(status=HTTPStatus.NO_CONTENT)


@require_GET  # type: ignore[misc]
def me(request: HttpRequest) -> HttpResponse:
    user_id = session_service.get_current_user_id(request)

    if user_id is None:
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    input = GetUserInput(user_id=user_id.value)
    output = get_user_use_case.execute(input)

    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.OK)


@require_POST  # type: ignore[misc]
def request_password_reset(request: HttpRequest) -> HttpResponse:
    data = json.loads(request.body)  # type: ignore[misc]
    email: str = data["email"]  # type: ignore[misc]
    request_password_reset_use_case.execute(email)

    return HttpResponse(status=HTTPStatus.NO_CONTENT)


@require_POST  # type: ignore[misc]
def reset_password(request: HttpRequest) -> JsonResponse:
    data = json.loads(request.body)  # type: ignore[misc]
    user_id: int = data["user_id"]  # type: ignore[misc]
    token: str = data["token"]  # type: ignore[misc]
    new_password: str = data["new_password"]  # type: ignore[misc]
    input_dto = ResetPasswordInput(
        user_id=user_id, token=token, new_password=new_password
    )
    output: UserOutput = reset_password_use_case.execute(input_dto)
    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.OK)


@require_POST  # type: ignore[misc]
def verify_email(request: HttpRequest) -> JsonResponse:
    data = json.loads(request.body)  # type: ignore[misc]
    user_id: int = data["user_id"]  # type: ignore[misc]
    token: str = data["token"]  # type: ignore[misc]
    input_dto = VerifyEmailInput(user_id=user_id, token=token)
    output: UserOutput = verify_email_use_case.execute(input_dto)
    return JsonResponse(UserPresenter.present(output), status=HTTPStatus.OK)
