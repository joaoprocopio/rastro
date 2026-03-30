from http import HTTPStatus

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET  # type: ignore[misc]
def conta(request: WSGIRequest) -> HttpResponse:
    return HttpResponse(status=HTTPStatus.IM_A_TEAPOT)
    # if not request.user.is_authenticated:  # type: ignore[union-attr]
    #     return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    # try:
    #     use_case = get_get_user_usecase()
    #     user = use_case.execute(_get_user_id(request))
    #     return JsonResponse(serialize_user(user), status=HTTPStatus.OK)
    # except UserNotFoundError:
    #     return HttpResponse(status=HTTPStatus.NOT_FOUND)


# @require_POST
# @csrf_exempt
# def entrar(request: WSGIRequest):
#     if request.user.is_authenticated:  # type: ignore[union-attr]
#         return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

#     try:
#         form = EntrarForm.model_validate_json(request.body)
#         use_case = get_authenticate_user_usecase()

#         user = use_case.execute(
#             AuthenticateUserInput(query=form.query, password=form.password)
#         )
#         auth_service.login(request, user)

#         return JsonResponse(serialize_user(user), status=HTTPStatus.OK)
#     except ValidationError as exc:
#         return HttpResponse(
#             exc.json().encode(),
#             status=HTTPStatus.BAD_REQUEST,
#             content_type="application/json",
#         )
#     except AuthenticationError:
#         return HttpResponse(status=HTTPStatus.UNAUTHORIZED)


# @require_POST
# @csrf_exempt
# def cadastrar(request: WSGIRequest):
#     if request.user.is_authenticated:  # type: ignore[union-attr]
#         return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

#     try:
#         form = CadastrarForm.model_validate_json(request.body)
#         use_case = create_user()

#         user = use_case.execute(
#             CreateUserInput(
#                 first_name=form.first_name,
#                 last_name=form.last_name,
#                 username=form.username,
#                 email=form.email,
#                 password=form.password,
#             )
#         )
#         auth_service.login(request, user)

#         return JsonResponse(serialize_user(user), status=HTTPStatus.OK)
#     except ValidationError as exc:
#         return HttpResponse(
#             exc.json().encode(),
#             status=HTTPStatus.BAD_REQUEST,
#             content_type="application/json",
#         )
#     except UserAlreadyExistsError:
#         return HttpResponse(status=HTTPStatus.CONFLICT)
#     except IntegrityError:
#         return HttpResponse(status=HTTPStatus.CONFLICT)


# @require_POST
# def sair(request: WSGIRequest):
#     if not request.user.is_authenticated:  # type: ignore[union-attr]
#         return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

#     auth_service.logout(request)
#     return HttpResponse(status=HTTPStatus.OK)
