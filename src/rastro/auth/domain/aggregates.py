from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Self

from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    HashedSessionToken,
    RawPassword,
    SessionLifetime,
    SessionToken,
)
from rastro.common.domain.aggregates import Aggregate
from rastro.common.domain.value_objects import Id

# The ports module imports the aggregates, so the import runs only for mypy.
if TYPE_CHECKING:
    from rastro.auth.domain.ports import PasswordHasher


class PasswordCheck(NamedTuple):
    is_correct: bool
    needs_rehash: bool


class User(Aggregate):
    id: Id
    email: Email
    display_name: DisplayName
    hashed_password: HashedPassword

    def verify_password(
        self, password: RawPassword, *, hasher: PasswordHasher
    ) -> PasswordCheck:
        return PasswordCheck(
            is_correct=hasher.verify(password=password, hashed=self.hashed_password),
            needs_rehash=hasher.needs_rehash(hashed=self.hashed_password),
        )


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
