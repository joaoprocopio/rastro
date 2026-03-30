from dataclasses import dataclass

from rastro.base.entities import Entity, Id
from rastro.users.value_objects import Email, Name, PasswordHash, Username


@dataclass
class User(Entity[Id]):
    username: Username
    email: Email
    password_hash: PasswordHash
    first_name: Name
    last_name: Name
