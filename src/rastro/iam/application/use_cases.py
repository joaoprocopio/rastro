from rastro.iam.application.dtos import (
    IdentityOutputDTO,
    RegisterIdentityInputDTO,
)
from rastro.iam.domain.repository import IdentityRepository
from rastro.iam.domain.services import PasswordHashingService, SessionService
from rastro.iam.shared.mappers import OutputIdentityMapper
from rastro_base.use_case import UseCase


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
