import json
from http import HTTPStatus

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from rastro.users.application.dtos import (
    ResetPasswordInput,
    SignInInput,
    SignUpInput,
    UserOutput,
    VerifyEmailInput,
)
from rastro.users.application.use_cases import (
    GetUserUseCase,
    ResetPasswordUseCase,
    SignInUseCase,
    SignUpUseCase,
    VerifyEmailUseCase,
)
from rastro.users.infrastructure.repository import DjangoUserRepository
from rastro.users.infrastructure.services import (
    DjangoPasswordHashingService,
)
from rastro.users.interfaces.presenters import UserPresenter

repository = DjangoUserRepository()
password_hashing_service = DjangoPasswordHashingService()

sign_up_use_case = SignUpUseCase(repository, password_hashing_service)
sign_in_use_case = SignInUseCase(repository, password_hashing_service)
get_user_use_case = GetUserUseCase(repository)
reset_password_use_case = ResetPasswordUseCase(
    repository, None, password_hashing_service
)
verify_email_use_case = VerifyEmailUseCase(repository, None)


@csrf_exempt
@require_POST
def sign_up(request: WSGIRequest) -> HttpResponse:
    data = json.loads(request.body)
    input = SignUpInput(
        username=data["username"],
        email=data["email"],
        password=data["password"],
    )
    output: UserOutput = sign_up_use_case.execute(input)
    public = UserPresenter.present(output)
    return JsonResponse(public, status=HTTPStatus.CREATED)


@csrf_exempt
@require_POST
def sign_in(request: WSGIRequest) -> HttpResponse:
    data = json.loads(request.body)
    input = SignInInput(
        query=data["query"],
        password=data["password"],
    )
    output: UserOutput = sign_in_use_case.execute(input)
    public = UserPresenter.present(output)
    return JsonResponse(public, status=HTTPStatus.OK)


@require_GET
def current_user(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    user_id = request.user.pk
    output: UserOutput = get_user_use_case.execute(user_id)
    public = UserPresenter.present(output)
    return JsonResponse(public, status=HTTPStatus.OK)


@csrf_exempt
@require_POST
def sign_out(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    from django.contrib.auth import logout

    logout(request)
    return HttpResponse(status=HTTPStatus.NO_CONTENT)


@csrf_exempt
@require_POST
def request_password_reset(request: WSGIRequest) -> HttpResponse:
    data = json.loads(request.body)
    email = data["email"]
    from rastro.users.application.use_cases import RequestPasswordResetUseCase

    use_case = RequestPasswordResetUseCase(repository, None)
    use_case.execute(email)
    return HttpResponse(status=HTTPStatus.NO_CONTENT)


@csrf_exempt
@require_POST
def reset_password(request: WSGIRequest) -> HttpResponse:
    data = json.loads(request.body)
    input = ResetPasswordInput(
        user_id=data["user_id"],
        token=data["token"],
        new_password=data["new_password"],
    )
    output: UserOutput = reset_password_use_case.execute(input)
    public = UserPresenter.present(output)
    return JsonResponse(public, status=HTTPStatus.OK)


@csrf_exempt
@require_POST
def verify_email(request: WSGIRequest) -> HttpResponse:
    data = json.loads(request.body)
    input = VerifyEmailInput(
        user_id=data["user_id"],
        token=data["token"],
    )
    output: UserOutput = verify_email_use_case.execute(input)
    public = UserPresenter.present(output)
    return JsonResponse(public, status=HTTPStatus.OK)
