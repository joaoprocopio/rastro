from functools import cache

from rastro.auth.domain.ports import (
    Clock,
    PasswordHasher,
    SessionRepository,
    UserRepository,
)
from rastro.auth.infrastructure.adapters import Argon2PasswordHasher, SystemClock
from rastro.auth.infrastructure.repositories import (
    SqlSessionRepository,
    SqlUserRepository,
)
from rastro.common.presentation.dependencies import DatabaseSession


# One instance per process, so the fixed hash of an unknown email is computed once.
@cache
def password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


def clock() -> Clock:
    return SystemClock()


def user_repository(db_session: DatabaseSession) -> UserRepository:
    return SqlUserRepository(db_session)


def session_repository(db_session: DatabaseSession) -> SessionRepository:
    return SqlSessionRepository(db_session)
