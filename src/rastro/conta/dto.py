from dataclasses import dataclass

from rastro.base.entities import Id
from rastro.conta.value_objects import Email, Name, PasswordHash, Username


@dataclass(frozen=True)
class EntrarInput:
    query: Email | Username
    password: PasswordHash


@dataclass(frozen=True)
class CadastrarInput:
    first_name: Name
    last_name: Name
    username: Username
    email: Email
    password: PasswordHash


@dataclass(frozen=True)
class ContaOutput:
    id: Id
    username: Username
    email: Email
    first_name: Name
    last_name: Name
