from rastro.conta.domain.entities import User
from rastro.conta.domain.exceptions import AuthenticationError
from rastro.conta.domain.repositories import UserRepository
from rastro.conta.domain.services import is_email
from rastro.conta.application.dto import AuthenticateUserInput, UserOutput


class AuthenticateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def execute(self, input: AuthenticateUserInput) -> UserOutput:
        if is_email(input.query):
            user = self._user_repo.get_by_email(input.query)
        else:
            user = self._user_repo.get_by_username(input.query)

        if user is None or not self._user_repo.verify_password(user, input.password):
            raise AuthenticationError()

        return UserOutput(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )


def get_authenticate_user_usecase() -> AuthenticateUserUseCase:
    from rastro.conta.infrastructure.repositories import DjangoUserRepository

    return AuthenticateUserUseCase(DjangoUserRepository())
