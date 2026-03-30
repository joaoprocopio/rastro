from dataclasses import dataclass

from rastro.base import AggregateRoot, Id
from rastro.users.domain.value_objects import Email, HashedPassword, Username


@dataclass
class User(AggregateRoot[Id]):
    username: Username
    email: Email
    hashed_password: HashedPassword
    is_active: bool = True
    is_verified: bool = False

    def update_email(self, email: Email) -> None:
        self.email = email

    def update_username(self, username: Username) -> None:
        self.username = username

    def update_password(self, hashed_password: HashedPassword) -> None:
        self.hashed_password = hashed_password

    def verify_email(self) -> None:
        self.is_verified = True

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False
