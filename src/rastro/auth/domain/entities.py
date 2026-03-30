from dataclasses import dataclass

from rastro.auth.domain.value_objects import Email, HashedPassword, Username
from rastro.base.entity import Entity, Id


@dataclass
class User(Entity[Id]):
    username: Username
    email: Email
    hashed_password: HashedPassword
    is_active: bool
