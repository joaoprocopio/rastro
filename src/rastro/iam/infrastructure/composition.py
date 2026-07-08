from django.http import HttpRequest

from rastro.iam.application.use_cases import (
    AuthenticateUseCase,
    EndSessionUseCase,
    GetCurrentIdentityUseCase,
    RegisterIdentityUseCase,
)
from rastro.iam.infrastructure.repositories import DjangoIdentityRepository
from rastro.iam.infrastructure.services import (
    DjangoPasswordHashingService,
    DjangoSessionService,
)


def django_get_current_identity_use_case_factory(
    request: HttpRequest,
) -> GetCurrentIdentityUseCase:
    session_service = DjangoSessionService(request)
    return GetCurrentIdentityUseCase(session_service)


def django_authenticate_use_case_factory(request: HttpRequest) -> AuthenticateUseCase:
    repository = DjangoIdentityRepository()
    password_hashing_service = DjangoPasswordHashingService()
    session_service = DjangoSessionService(request)
    return AuthenticateUseCase(repository, session_service, password_hashing_service)


def django_register_identity_use_case_factory(
    request: HttpRequest,
) -> RegisterIdentityUseCase:
    repository = DjangoIdentityRepository()
    password_hashing_service = DjangoPasswordHashingService()
    session_service = DjangoSessionService(request)
    return RegisterIdentityUseCase(
        repository, session_service, password_hashing_service
    )


def django_end_session_use_case_factory(request: HttpRequest) -> EndSessionUseCase:
    session_service = DjangoSessionService(request)
    return EndSessionUseCase(session_service)
