from datetime import datetime
from typing import Optional

from rastro.conta.domain.services import PasswordHashingService, PasswordVerification
from rastro.conta.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    RawPassword,
)
from rastro_base.aggregate import AggregateRoot
from rastro_shared_kernel.value_objects import Id


class Conta(AggregateRoot):
    id: Id
    email: Email
    password: HashedPassword
    display_name: DisplayName
    date_joined: datetime
    last_login: Optional[datetime]
    is_active: bool
    is_staff: bool
    is_superuser: bool

    def set_password(
        self,
        raw_password: RawPassword,
        password_hashing_service: PasswordHashingService,
    ) -> None:
        self.password = password_hashing_service.hash(raw_password)

    def verify_password(
        self,
        raw_password: RawPassword,
        password_hashing_service: PasswordHashingService,
    ) -> PasswordVerification:
        verification = password_hashing_service.verify(raw_password, self.password)

        if verification.is_correct and verification.must_upgrade:
            self.set_password(raw_password, password_hashing_service)

        return verification
