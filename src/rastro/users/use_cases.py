from rastro.base.use_cases import UseCase
from rastro.users.dto import SignInInput, SignUpInput, UserOutput
from rastro.users.entities import User
from rastro.users.errors import (
    AuthenticationError,
)
from rastro.users.mappers import UserToDTOMapper
from rastro.users.repository import UserRepository
from rastro.users.value_objects import Email, Password, Username


class SignUpUseCase(UseCase[SignUpInput, UserOutput]):
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, input: SignUpInput) -> UserOutput:
        user = self.repository.save(
            User(
                id=None,
                username=Username(input.username),
                email=Email(input.email),
                password=Password(input.password),
            )
        )

        return UserToDTOMapper.map(user)


class SignInUseCase(UseCase[SignInInput, UserOutput]):
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, input: SignInInput) -> UserOutput:
        if "@" in input.query:
            user = self.repository.get_by_email(input.query)
        else:
            user = self.repository.get_by_username(input.query)

        if user is None:
            raise AuthenticationError("Invalid credentials")

        if not self.repository.verify_password(user, user.password.value):
            raise AuthenticationError("Invalid credentials")

        return UserToDTOMapper.map(user)
