from rastro.auth.application.dtos import (
    SignInInput,
    SignUpInput,
    UserOutput,
)
from rastro.auth.domain.errors import (
    AuthenticationError,
    UserNotFoundError,
)
from rastro.auth.domain.repository import UserRepository
from rastro.auth.domain.services import PasswordHashingService
from rastro.auth.domain.value_objects import (
    Email,
    RawPassword,
    Username,
)
from rastro.auth.infrastructure.mappers import DomainToOutputUserMapper
from rastro_base.use_case import UseCase


class SignUpUseCase(UseCase[SignUpInput, UserOutput]):
    def __init__(
        self,
        repository: UserRepository,
        password_hashing_service: PasswordHashingService,
    ):
        self.repository = repository
        self.password_hashing_service = password_hashing_service

    def execute(self, input: SignUpInput) -> UserOutput:
        raw_password = RawPassword(input.password).validate()
        hashed_password = self.password_hashing_service.hash(raw_password)

        user = self.repository.create(
            username=Username(input.username).validate().normalize(),
            email=Email(input.email).validate().normalize(),
            hashed_password=hashed_password,
        )

        return DomainToOutputUserMapper.map(user)


class SignInUseCase(UseCase[SignInInput, UserOutput]):
    def __init__(
        self,
        repository: UserRepository,
        password_hashing_service: PasswordHashingService,
    ):
        self.repository = repository
        self.password_hashing_service = password_hashing_service

    def execute(self, input: SignInInput) -> UserOutput:
        if "@" in input.query:
            user = self.repository.get_by_email(Email(input.query))
        else:
            user = self.repository.get_by_username(Username(input.query))

        if user is None:
            raise UserNotFoundError()

        raw_password = RawPassword(input.password)

        if not self.password_hashing_service.verify(raw_password, user.hashed_password):
            raise AuthenticationError()

        return DomainToOutputUserMapper.map(user)
