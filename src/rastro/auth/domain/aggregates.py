from datetime import datetime, timedelta
from typing import TYPE_CHECKING, NamedTuple, Self

from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    RawPassword,
    SessionToken,
    SessionTokenHash,
)
from rastro.common.domain.aggregates import Aggregate

# The ports module imports the aggregates, so the import runs only for mypy.
if TYPE_CHECKING:
    from rastro.auth.domain.ports import PasswordHasher

# A Session ends this long after it starts, with no renewal on use.
SESSION_LIFETIME = timedelta(days=14)


class PasswordCheck(NamedTuple):
    is_correct: bool
    needs_rehash: bool


class User(Aggregate):
    id: int
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
    id: int
    user_id: int
    token_hash: SessionTokenHash
    expires_at: datetime

    @classmethod
    def start(cls, *, id: int, user_id: int, token: SessionToken, at: datetime) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            token_hash=token.digest(),
            expires_at=at + SESSION_LIFETIME,
        )

    def is_active(self, *, at: datetime) -> bool:
        return at < self.expires_at
