from typing import TypedDict

from rastro.base.presenters import Presenter
from rastro.conta.dto import ContaOutput


class ContaPublic(TypedDict):
    email: str
    username: str
    first_name: str
    last_name: str


class ContaPresenter(Presenter[ContaOutput, ContaPublic]):
    @staticmethod
    def present(private: ContaOutput) -> ContaPublic:
        return ContaPublic(
            email=private.email,
            username=private.username,
            first_name=private.first_name,
            last_name=private.last_name,
        )
