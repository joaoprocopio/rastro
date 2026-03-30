from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import TYPE_CHECKING

from rastro.auth.domain.events import (
    PasswordChanged,
    UserActivated,
    UserCreated,
    UserDeactivated,
    UserLoggedIn,
)
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    RawPassword,
    Username,
)
from rastro_base.entity import Entity, Id

if TYPE_CHECKING:
    from rastro.auth.domain.services import PasswordHashingService


@dataclass
class User(Entity[Id]):
    username: Username
    email: Email
    _hashed_password: HashedPassword
    is_active: bool = True
    last_login: datetime | None = field(default=None, init=False)

    @classmethod
    def create(
        cls,
        id: Id,
        username: Username,
        email: Email,
        hashed_password: HashedPassword,
    ) -> "User":
        user = cls(
            id=id, username=username, email=email, _hashed_password=hashed_password
        )
        user.add_domain_event(
            UserCreated(user_id=id.value, username=username.value, email=email.value)
        )
        return user

    def set_password(
        self, raw_password: RawPassword, hashing_service: "PasswordHashingService"
    ) -> None:
        raw_password.validate()
        self._hashed_password = hashing_service.hash(raw_password)
        self.add_domain_event(PasswordChanged(user_id=self.id.value))

    def verify_password(
        self, raw_password: RawPassword, hashing_service: "PasswordHashingService"
    ) -> bool:
        return hashing_service.verify(raw_password, self._hashed_password)

    def activate(self) -> None:
        if not self.is_active:
            self.is_active = True
            self.add_domain_event(UserActivated(user_id=self.id.value))

    def deactivate(self) -> None:
        if self.is_active:
            self.is_active = False
            self.add_domain_event(UserDeactivated(user_id=self.id.value))

    def record_login(self) -> None:
        self.last_login = datetime.now(UTC)
        self.add_domain_event(UserLoggedIn(user_id=self.id.value))

    def update_email(self, email: Email) -> None:
        self.email = email

    @property
    def hashed_password(self) -> str:
        return self._hashed_password.value
