from http import HTTPStatus
from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View

from rastro.iam.application.dtos import RegisterIdentityInputDTO
from rastro.iam.application.use_cases import RegisterIdentityUseCase
from rastro.iam.infrastructure.composition import (
    django_register_identity_use_case_factory,
)
from rastro.iam.shared.mappers import PresentIdentityMapper


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
