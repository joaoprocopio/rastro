from rastro.conta.domain.entities import User
from rastro.conta.domain.exceptions import (
    UserAlreadyExistsError as DomainUserAlreadyExistsError,
)
from rastro.conta.domain.repositories import UserRepository
from rastro.conta.application.dto import CreateUserInput, UserOutput
from rastro.conta.application.exceptions import UserAlreadyExistsError


class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def execute(self, input: CreateUserInput) -> UserOutput:
        existing_user = self._user_repo.get_by_email(input.email)
        if existing_user is None:
            existing_user = self._user_repo.get_by_username(input.username)

        if existing_user is not None:
            raise UserAlreadyExistsError()

        user = self._user_repo.create(
            first_name=input.first_name,
            last_name=input.last_name,
            username=input.username,
            email=input.email,
            password=input.password,
        )

        return UserOutput(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )


def get_create_user_usecase() -> CreateUserUseCase:
    from rastro.conta.infrastructure.repositories import DjangoUserRepository

    return CreateUserUseCase(DjangoUserRepository())
