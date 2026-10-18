from django.http import HttpRequest

from rastro.iam.application.use_cases import (
    EndSessionUseCase,
    GetCurrentIdentityUseCase,
)
from rastro.iam.infrastructure.services import DjangoSessionService


def django_get_current_identity_use_case_factory(
    request: HttpRequest,
) -> GetCurrentIdentityUseCase:
    session_service = DjangoSessionService(request)
    return GetCurrentIdentityUseCase(session_service)


def django_end_session_use_case_factory(request: HttpRequest) -> EndSessionUseCase:
    session_service = DjangoSessionService(request)
    return EndSessionUseCase(session_service)
