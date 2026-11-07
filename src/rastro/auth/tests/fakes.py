import re
from datetime import datetime

from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.errors import EmailInUseError
from rastro.auth.domain.ports import PasswordCheck
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    HashedResetToken,
    HashedSessionToken,
    OutgoingEmail,
    RawPassword,
    ResetToken,
)
from rastro.common.domain.value_objects import Id

CURRENT_SCHEME = "fake"


class FakePasswordHasher:
    """Hashes to `<scheme>$<password>`, and a scheme other than `fake` is outdated."""

    def __init__(self) -> None:
        self.hashed: list[RawPassword] = []
        self.verified: list[tuple[RawPassword, HashedPassword | None]] = []

    def hash(self, *, password: RawPassword) -> HashedPassword:
        self.hashed.append(password)
        return HashedPassword(f"{CURRENT_SCHEME}${password.root.get_secret_value()}")

    def verify(
        self, *, password: RawPassword, hashed: HashedPassword | None
    ) -> PasswordCheck:
        self.verified.append((password, hashed))
        if hashed is None:
            return PasswordCheck(is_correct=False, new_hash=None)
        scheme, _, secret = hashed.root.partition("$")
        if secret != password.root.get_secret_value():
            return PasswordCheck(is_correct=False, new_hash=None)
        if scheme != CURRENT_SCHEME:
            return PasswordCheck(is_correct=True, new_hash=self.hash(password=password))
        return PasswordCheck(is_correct=True, new_hash=None)


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[Id, User] = {}
        self._last_id = 0

    async def next_id(self) -> Id:
        self._last_id += 1
        return Id(self._last_id)

    async def add(self, user: User) -> None:
        self._store(user)

    async def update(self, user: User) -> None:
        if user.id not in self.users:
            raise LookupError(f"No User with the id {user.id.root}.")
        self._store(user)

    async def get_by_id(self, id: Id) -> User | None:
        user = self.users.get(id)
        return None if user is None else user.model_copy()

    async def get_by_email(self, email: Email) -> User | None:
        return next(
            (user.model_copy() for user in self.users.values() if user.email == email),
            None,
        )

    def _store(self, user: User) -> None:
        if any(
            stored.email == user.email and stored.id != user.id
            for stored in self.users.values()
        ):
            raise EmailInUseError()
        self.users[user.id] = user.model_copy()


class FakeSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[Id, Session] = {}
        self._last_id = 0

    async def next_id(self) -> Id:
        self._last_id += 1
        return Id(self._last_id)

    async def add(self, session: Session) -> None:
        self.sessions[session.id] = session.model_copy()

    async def remove(self, session: Session) -> None:
        if session.id not in self.sessions:
            raise LookupError(f"No Session with the id {session.id.root}.")
        del self.sessions[session.id]

    async def remove_by_user_id(self, user_id: Id) -> None:
        self.sessions = {
            id: session
            for id, session in self.sessions.items()
            if session.user_id != user_id
        }

    async def remove_expired(self, *, at: datetime) -> int:
        expired = [
            id for id, session in self.sessions.items() if not session.is_active(at=at)
        ]
        for id in expired:
            del self.sessions[id]
        return len(expired)

    async def get_by_hashed_token(
        self, hashed_token: HashedSessionToken
    ) -> Session | None:
        return next(
            (
                session.model_copy()
                for session in self.sessions.values()
                if session.hashed_token == hashed_token
            ),
            None,
        )


class FakeResetTokenRepository:
    def __init__(self) -> None:
        self.reset_tokens: dict[Id, IssuedResetToken] = {}
        self._last_id = 0

    async def next_id(self) -> Id:
        self._last_id += 1
        return Id(self._last_id)

    async def replace(self, reset_token: IssuedResetToken) -> None:
        self.reset_tokens[reset_token.user_id] = reset_token.model_copy()

    async def get_by_user_id(self, user_id: Id) -> IssuedResetToken | None:
        reset_token = self.reset_tokens.get(user_id)
        return None if reset_token is None else reset_token.model_copy()

    async def consume(self, hashed_token: HashedResetToken) -> IssuedResetToken | None:
        for user_id, reset_token in self.reset_tokens.items():
            if reset_token.hashed_token == hashed_token:
                del self.reset_tokens[user_id]
                return reset_token
        return None


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[OutgoingEmail] = []
        self.error: Exception | None = None

    async def send(self, email: OutgoingEmail) -> None:
        if self.error is not None:
            raise self.error
        self.sent.append(email)

    def last_reset_token(self) -> ResetToken:
        """The Reset token in the link of the last email."""
        match = re.search(r"#token=(\S+)", self.sent[-1].body.get_secret_value())
        assert match is not None
        return ResetToken.model_validate(match[1])


class FakePasswordResetJobs:
    def __init__(self) -> None:
        self.deferred_sends: list[Email] = []

    async def defer_send(self, email: Email) -> None:
        self.deferred_sends.append(email)
