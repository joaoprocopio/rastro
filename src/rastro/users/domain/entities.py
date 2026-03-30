from dataclasses import dataclass

from rastro.base.entity import Entity, Id
from rastro.users.domain.value_objects import Email, HashedPassword, Username


@dataclass
class User(Entity[Id]):
    username: Username
    email: Email
    hashed_password: HashedPassword
    is_active: bool
