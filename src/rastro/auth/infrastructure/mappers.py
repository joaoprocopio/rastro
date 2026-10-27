from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    SessionTokenHash,
)
from rastro.auth.infrastructure.models import SessionRow, UserRow


def user_from_row(row: UserRow) -> User:
    return User(
        id=row.id,
        email=Email.model_validate(row.email),
        display_name=DisplayName.model_validate(row.display_name),
        hashed_password=HashedPassword.model_validate(row.hashed_password),
    )


def user_to_row(user: User) -> UserRow:
    return UserRow(
        id=user.id,
        email=user.email.root,
        display_name=user.display_name.root,
        hashed_password=user.hashed_password.root,
    )


def session_from_row(row: SessionRow) -> Session:
    return Session(
        id=row.id,
        user_id=row.user_id,
        token_hash=SessionTokenHash.model_validate(row.token_hash),
        expires_at=row.expires_at,
    )


def session_to_row(session: Session) -> SessionRow:
    return SessionRow(
        id=session.id,
        user_id=session.user_id,
        token_hash=session.token_hash.root,
        expires_at=session.expires_at,
    )
