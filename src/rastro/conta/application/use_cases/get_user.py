from typing import Optional

from rastro.conta.domain.entities import User
from rastro.conta.domain.exceptions import UserNotFoundError
from rastro.conta.domain.repositories import UserRepository
from rastro.conta.application.dto import UserOutput


class GetUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def execute(self, user_id: int) -> UserOutput:
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return UserOutput(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )


def get_get_user_usecase() -> GetUserUseCase:
    from rastro.conta.infrastructure.repositories import DjangoUserRepository

    return GetUserUseCase(DjangoUserRepository())
