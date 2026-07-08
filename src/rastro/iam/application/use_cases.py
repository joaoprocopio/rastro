from typing import Optional

from rastro.iam.application.dtos import (
    AuthenticateInputDTO,
    IdentityOutputDTO,
    RegisterIdentityInputDTO,
)
from rastro.iam.domain.errors import IncorrectCredentialsError
from rastro.iam.domain.repository import IdentityRepository
from rastro.iam.domain.services import PasswordHashingService, SessionService
from rastro.iam.shared.mappers import OutputIdentityMapper
from rastro_base.use_case import UseCase


class GetCurrentIdentityUseCase(UseCase):
    def __init__(
        self,
        session_service: SessionService,
    ):
        self.session_service = session_service

    def execute(self) -> Optional[IdentityOutputDTO]:
        identity = self.session_service.current_identity()

        if identity is None:
            return None

        return OutputIdentityMapper.map(identity)


class RegisterIdentityUseCase(UseCase):
    def __init__(
        self,
        repository: IdentityRepository,
        session_service: SessionService,
        password_hashing_service: PasswordHashingService,
    ):
        self.repository = repository
        self.session_service = session_service
        self.password_hashing_service = password_hashing_service

    def execute(self, input: RegisterIdentityInputDTO) -> IdentityOutputDTO:
        hashed_password = self.password_hashing_service.hash(input.password)

        identity = self.repository.create(
            display_name=input.display_name,
            email=input.email,
            hashed_password=hashed_password,
        )

        self.session_service.start(identity)

        return OutputIdentityMapper.map(identity)


class AuthenticateUseCase(UseCase):
    def __init__(
        self,
        repository: IdentityRepository,
        session_service: SessionService,
        password_hashing_service: PasswordHashingService,
    ):
        self.repository = repository
        self.session_service = session_service
        self.password_hashing_service = password_hashing_service

    def execute(self, input: AuthenticateInputDTO) -> IdentityOutputDTO:
        identity = self.repository.get_by_email(input.email)

        if identity is None:
            raise IncorrectCredentialsError("Incorrect email or password.")

        verification = identity.verify_password(
            input.password, self.password_hashing_service
        )

        if not verification.is_correct:
            raise IncorrectCredentialsError("Incorrect email or password.")

        if verification.must_upgrade:
            self.repository.update_password(identity)

        self.session_service.start(identity)

        return OutputIdentityMapper.map(identity)


class EndSessionUseCase(UseCase):
    def __init__(self, session_service: SessionService):
        self.session_service = session_service

    def execute(self) -> None:
        self.session_service.end()
