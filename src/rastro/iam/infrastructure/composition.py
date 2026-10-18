from django.http import HttpRequest

from rastro.iam.application.use_cases import RegisterIdentityUseCase
from rastro.iam.infrastructure.repositories import DjangoIdentityRepository
from rastro.iam.infrastructure.services import (
    DjangoPasswordHashingService,
    DjangoSessionService,
)


def django_register_identity_use_case_factory(
    request: HttpRequest,
) -> RegisterIdentityUseCase:
    repository = DjangoIdentityRepository()
    password_hashing_service = DjangoPasswordHashingService()
    session_service = DjangoSessionService(request)
    return RegisterIdentityUseCase(
        repository, session_service, password_hashing_service
    )
