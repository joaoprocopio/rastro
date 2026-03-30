from dataclasses import dataclass

from rastro.base.entities import Entity, Id
from rastro.conta.value_objects import Email, Name, PasswordHash, Username


@dataclass
class Conta(Entity[Id]):
    username: Username
    email: Email
    password_hash: PasswordHash
    first_name: Name
    last_name: Name
