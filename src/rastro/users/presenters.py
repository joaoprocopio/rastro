from typing import TypedDict

from rastro.base.presenters import Presenter
from rastro.users.dto import UserOutput


class UserPublic(TypedDict):
    email: str
    username: str
    first_name: str
    last_name: str


class UserPresenter(Presenter[UserOutput, UserPublic]):
    @staticmethod
    def to_public(private: UserOutput) -> UserPublic:
        return UserPublic(
            email=private.email,
            username=private.username,
            first_name=private.first_name,
            last_name=private.last_name,
        )
