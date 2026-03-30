from rastro.base.entity import Id
from rastro.base.use_case import UseCase
from rastro.users.application.dtos import (
    GetUserInput,
    SignInInput,
    SignUpInput,
    UserOutput,
)
from rastro.users.domain.errors import (
    AuthenticationError,
    UserNotFoundError,
)
from rastro.users.domain.repository import UserRepository
from rastro.users.domain.services import PasswordHashingService
from rastro.users.domain.value_objects import Email, RawPassword, Username
from rastro.users.infrastructure.mappers import DomainUserToOutputMapper


class SignUpUseCase(UseCase[SignUpInput, UserOutput]):
    def __init__(
        self,
        repository: UserRepository,
    ):
        self.repository = repository

    def execute(self, input: SignUpInput) -> UserOutput:
        user = self.repository.create(  # type: ignore
            username=Username(input.username),
            email=Email(input.email),
            raw_password=RawPassword(input.password),
        )

        return DomainUserToOutputMapper.map(user)


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
            raise AuthenticationError("Invalid credentials")

        return DomainUserToOutputMapper.map(user)


class GetUserUseCase(UseCase[GetUserInput, UserOutput]):
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, input: GetUserInput) -> UserOutput:
        user_id = Id(input.user_id)
        user = self.repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError(f"User with id {input.user_id} not found")

        return DomainUserToOutputMapper.map(user)
