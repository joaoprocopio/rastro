from dataclasses import dataclass

from rastro.base.entities import Id
from rastro.conta.value_objects import Email, Name, Password, Username


@dataclass(frozen=True)
class EntrarInput:
    query: Email | Username
    password: Password


@dataclass(frozen=True)
class CadastrarInput:
    first_name: Name
    last_name: Name
    username: Username
    email: Email
    password: Password


@dataclass(frozen=True)
class ContaOutput:
    id: Id
    username: Username
    email: Email
    first_name: Name
    last_name: Name

    def __dict__(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }
