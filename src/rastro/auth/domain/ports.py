from datetime import datetime
from typing import NamedTuple, Protocol

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    HashedSessionToken,
    RawPassword,
)
from rastro.common.domain.value_objects import Id


class PasswordCheck(NamedTuple):
    is_correct: bool
    new_hash: HashedPassword | None


class PasswordHasher(Protocol):
    def hash(self, *, password: RawPassword) -> HashedPassword: ...

    # No hash (an unknown email) takes as long as a wrong password and is never correct.
    def verify(
        self, *, password: RawPassword, hashed: HashedPassword | None
    ) -> PasswordCheck: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class UserRepository(Protocol):
    async def next_id(self) -> Id: ...

    async def add(self, user: User) -> None: ...

    async def update(self, user: User) -> None: ...

    async def remove(self, user: User) -> None: ...

    async def get_by_id(self, id: Id) -> User | None: ...

    async def get_by_email(self, email: Email) -> User | None: ...


class SessionRepository(Protocol):
    async def next_id(self) -> Id: ...

    async def add(self, session: Session) -> None: ...

    async def update(self, session: Session) -> None: ...

    async def remove(self, session: Session) -> None: ...

    async def get_by_id(self, id: Id) -> Session | None: ...

    async def get_by_hashed_token(
        self, hashed_token: HashedSessionToken
    ) -> Session | None: ...
