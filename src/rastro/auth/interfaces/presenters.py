from typing import TypedDict

from rastro.auth.application.dtos import UserOutput
from rastro.base.presenter import Presenter


class UserPublic(TypedDict):
    email: str
    username: str


class UserPresenter(Presenter[UserOutput, UserPublic]):
    @staticmethod
    def present(private: UserOutput) -> UserPublic:
        return UserPublic(
            email=private.email,
            username=private.username,
        )
