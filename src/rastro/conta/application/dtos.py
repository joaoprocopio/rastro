from datetime import datetime
from typing import Optional

from rastro.conta.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    RawPassword,
)
from rastro_base.dto import DTO
from rastro_shared_kernel.value_objects import Id


class CadastrarInput(DTO):
    display_name: DisplayName
    email: Email
    password: RawPassword


class EntrarInput(DTO):
    email: Email
    password: RawPassword


class ContaOutput(DTO):
    id: Id
    email: Email
    password: HashedPassword
    display_name: DisplayName
    date_joined: datetime
    last_login: Optional[datetime]
    is_active: bool
    is_staff: bool
    is_superuser: bool


class ContaPublic(DTO):
    display_name: DisplayName
    email: Email
