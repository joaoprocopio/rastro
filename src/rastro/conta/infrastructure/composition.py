from django.http import HttpRequest

from rastro.conta.application.use_cases import (
    CadastrarUseCase,
    ContaUseCase,
    EntrarUseCase,
    SairUseCase,
)
from rastro.conta.infrastructure.repositories import DjangoContaRepository
from rastro.conta.infrastructure.services import (
    DjangoPasswordHashingService,
    DjangoSessionService,
)


def django_conta_use_case_factory(request: HttpRequest) -> ContaUseCase:
    session_service = DjangoSessionService(request)
    conta_use_case = ContaUseCase(session_service)

    return conta_use_case


def django_entrar_use_case_factory(request: HttpRequest) -> EntrarUseCase:
    repository = DjangoContaRepository()
    password_hashing_service = DjangoPasswordHashingService()
    session_service = DjangoSessionService(request)
    entrar_use_case = EntrarUseCase(
        repository, session_service, password_hashing_service
    )

    return entrar_use_case


def django_cadastrar_use_case_factory(request: HttpRequest) -> CadastrarUseCase:
    repository = DjangoContaRepository()
    password_hashing_service = DjangoPasswordHashingService()
    session_service = DjangoSessionService(request)
    cadastrar_use_case = CadastrarUseCase(
        repository, session_service, password_hashing_service
    )

    return cadastrar_use_case


def django_sair_use_case_factory(request: HttpRequest) -> SairUseCase:
    session_service = DjangoSessionService(request)
    sair_use_case = SairUseCase(session_service)

    return sair_use_case
