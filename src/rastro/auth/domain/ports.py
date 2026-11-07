from datetime import datetime
from typing import NamedTuple, Protocol

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    HashedResetToken,
    HashedSessionToken,
    OutgoingEmail,
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

    async def get_by_id(self, id: Id) -> User | None: ...

    async def get_by_email(self, email: Email) -> User | None: ...


class SessionRepository(Protocol):
    async def next_id(self) -> Id: ...

    async def add(self, session: Session) -> None: ...

    async def remove(self, session: Session) -> None: ...

    async def remove_by_user_id(self, user_id: Id) -> None: ...

    async def remove_expired(self, *, at: datetime) -> int: ...

    async def get_by_hashed_token(
        self, hashed_token: HashedSessionToken
    ) -> Session | None: ...


class ResetTokenRepository(Protocol):
    async def next_id(self) -> Id: ...

    # A User holds one Reset token, so a new one takes the place of the last one.
    async def replace(self, reset_token: IssuedResetToken) -> None: ...

    async def get_by_user_id(self, user_id: Id) -> IssuedResetToken | None: ...

    # Removes and returns the token in one step, so only one caller can use it.
    async def consume(
        self, hashed_token: HashedResetToken
    ) -> IssuedResetToken | None: ...

    async def remove_expired(self, *, at: datetime) -> int: ...


class EmailSender(Protocol):
    # Raises EmailTemporaryError, EmailRefusedError, or EmailNoAnswerError.
    async def send(self, email: OutgoingEmail) -> None: ...


class PasswordResetJobs(Protocol):
    # The job commits or rolls back with the transaction of the caller.
    async def defer_send(self, email: Email) -> None: ...
