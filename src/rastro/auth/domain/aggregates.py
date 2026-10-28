from datetime import datetime
from typing import Self

from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    HashedSessionToken,
    SessionLifetime,
    SessionToken,
)
from rastro.common.domain.aggregates import Aggregate
from rastro.common.domain.value_objects import Id


class User(Aggregate):
    id: Id
    email: Email
    display_name: DisplayName
    hashed_password: HashedPassword


class Session(Aggregate):
    id: Id
    user_id: Id
    hashed_token: HashedSessionToken
    expires_at: datetime

    @classmethod
    def start(
        cls,
        *,
        id: Id,
        user_id: Id,
        token: SessionToken,
        at: datetime,
        lifetime: SessionLifetime,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            hashed_token=token.digest(),
            expires_at=at + lifetime.root,
        )

    def is_active(self, *, at: datetime) -> bool:
        return at < self.expires_at
