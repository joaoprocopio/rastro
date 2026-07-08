from typing import Optional

from rastro.conta.application.dtos import (
    CadastrarInput,
    ContaOutput,
    EntrarInput,
)
from rastro.conta.domain.errors import (
    ContaNaoEncontradaError,
    CredenciaisIncorretasError,
)
from rastro.conta.domain.repository import ContaRepository
from rastro.conta.domain.services import PasswordHashingService, SessionService
from rastro.conta.shared.mappers import OutputContaMapper
from rastro_base.use_case import UseCase


class ContaUseCase(UseCase):
    def __init__(
        self,
        session_service: SessionService,
    ):
        self.session_service = session_service

    def execute(self) -> Optional[ContaOutput]:
        conta = self.session_service.logged_conta()

        if conta is None:
            return None

        return OutputContaMapper.map(conta)


class CadastrarUseCase(UseCase):
    def __init__(
        self,
        repository: ContaRepository,
        session_service: SessionService,
        password_hashing_service: PasswordHashingService,
    ):
        self.repository = repository
        self.session_service = session_service
        self.password_hashing_service = password_hashing_service

    def execute(self, input: CadastrarInput) -> ContaOutput:
        hashed_password = self.password_hashing_service.hash(input.password)

        conta = self.repository.create(
            display_name=input.display_name,
            email=input.email,
            hashed_password=hashed_password,
        )

        self.session_service.login(conta)

        return OutputContaMapper.map(conta)


class EntrarUseCase(UseCase):
    def __init__(
        self,
        repository: ContaRepository,
        session_service: SessionService,
        password_hashing_service: PasswordHashingService,
    ):
        self.repository = repository
        self.session_service = session_service
        self.password_hashing_service = password_hashing_service

    def execute(self, input: EntrarInput) -> ContaOutput:
        conta = self.repository.get_by_email(input.email)

        if conta is None:
            raise ContaNaoEncontradaError(
                "Nenhuma conta encontrada para o email informado."
            )

        verification = conta.verify_password(
            input.password, self.password_hashing_service
        )

        if not verification.is_correct:
            raise CredenciaisIncorretasError("Email ou senha incorretos.")

        if verification.must_upgrade:
            self.repository.update_password(conta)

        self.session_service.login(conta)

        return OutputContaMapper.map(conta)


class SairUseCase(UseCase):
    def __init__(self, session_service: SessionService):
        self.session_service = session_service

    def execute(self) -> None:
        self.session_service.logout()
