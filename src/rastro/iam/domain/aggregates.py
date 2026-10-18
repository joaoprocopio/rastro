from datetime import datetime
from typing import Optional

from rastro.iam.values import (
    DisplayName,
    Email,
    HashedPassword,
)
from rastro_base.aggregate import AggregateRoot
from rastro_shared_kernel.value_objects import Id


class IdentityAggregate(AggregateRoot):
    id: Id
    email: Email
    password: HashedPassword
    display_name: DisplayName
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    is_staff: bool
    is_superuser: bool
