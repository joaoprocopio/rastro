from datetime import datetime
from typing import Optional

from rastro.iam.values import (
    DisplayName,
    Email,
)
from rastro_base.dto import DTO
from rastro_shared_kernel.value_objects import Id


class IdentityOutputDTO(DTO):
    id: Id
    email: Email
    display_name: DisplayName
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    is_staff: bool
    is_superuser: bool


class IdentityPublicDTO(DTO):
    display_name: DisplayName
    email: Email
