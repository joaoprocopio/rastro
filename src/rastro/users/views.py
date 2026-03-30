from http import HTTPStatus

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from rastro.users.mappers import DjangoUserMapper, DTOUserMapper
from rastro.users.presenters import UserPresenter
from rastro.users.repository import DjangoUserRepository
from rastro.users.use_cases import SignInUseCase, SignUpUseCase

repository = DjangoUserRepository()
entrar_use_case = SignInUseCase(repository)
cadastrar_use_case = SignUpUseCase(repository)


@require_GET  # type: ignore[misc]
def current_user(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return HttpResponse(status=HTTPStatus.UNAUTHORIZED)

    user_entity = DjangoUserMapper.to_source(request.user)
    user_dto = DTOUserMapper.to_source(user_entity)
    user_public = UserPresenter.to_public(user_dto)

    return JsonResponse(user_public, status=HTTPStatus.OK)
