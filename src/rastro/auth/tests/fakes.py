from datetime import datetime

from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    HashedSessionToken,
    RawPassword,
)
from rastro.common.domain.value_objects import Id

CURRENT_SCHEME = "fake"


class FakePasswordHasher:
    """Hashes to `<scheme>$<password>`, and a scheme other than `fake` is outdated."""

    def __init__(self) -> None:
        self.hashed: list[RawPassword] = []
        self.verified: list[tuple[RawPassword, HashedPassword]] = []

    @property
    def fixed_hash(self) -> HashedPassword:
        return HashedPassword(f"{CURRENT_SCHEME}$fixed")

    def hash(self, *, password: RawPassword) -> HashedPassword:
        self.hashed.append(password)
        return HashedPassword(f"{CURRENT_SCHEME}${password.root.get_secret_value()}")

    def verify(self, *, password: RawPassword, hashed: HashedPassword) -> bool:
        self.verified.append((password, hashed))
        return hashed.root.partition("$")[2] == password.root.get_secret_value()

    def needs_rehash(self, *, hashed: HashedPassword) -> bool:
        return hashed.root.partition("$")[0] != CURRENT_SCHEME


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[Id, User] = {}
        self._last_id = 0

    async def next_id(self) -> Id:
        self._last_id += 1
        return Id(self._last_id)

    async def add(self, user: User) -> None:
        self.users[user.id] = user.model_copy()

    async def update(self, user: User) -> None:
        if user.id not in self.users:
            raise LookupError(f"No User with the id {user.id.root}.")
        self.users[user.id] = user.model_copy()

    async def remove(self, user: User) -> None:
        del self.users[user.id]

    async def get_by_id(self, id: Id) -> User | None:
        user = self.users.get(id)
        return None if user is None else user.model_copy()

    async def get_by_email(self, email: Email) -> User | None:
        return next(
            (user.model_copy() for user in self.users.values() if user.email == email),
            None,
        )


class FakeSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[Id, Session] = {}
        self._last_id = 0

    async def next_id(self) -> Id:
        self._last_id += 1
        return Id(self._last_id)

    async def add(self, session: Session) -> None:
        self.sessions[session.id] = session.model_copy()

    async def update(self, session: Session) -> None:
        if session.id not in self.sessions:
            raise LookupError(f"No Session with the id {session.id.root}.")
        self.sessions[session.id] = session.model_copy()

    async def remove(self, session: Session) -> None:
        del self.sessions[session.id]

    async def get_by_id(self, id: Id) -> Session | None:
        session = self.sessions.get(id)
        return None if session is None else session.model_copy()

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


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current
