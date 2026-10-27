from rastro.auth.domain.aggregates import Session, User
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    HashedSessionToken,
)
from rastro.auth.infrastructure.models import SessionRow, UserRow
from rastro.common.domain.value_objects import Id


def user_from_row(row: UserRow) -> User:
    return User(
        id=Id.model_validate(row.id),
        email=Email.model_validate(row.email),
        display_name=DisplayName.model_validate(row.display_name),
        hashed_password=HashedPassword.model_validate(row.hashed_password),
    )


def user_to_row(user: User) -> UserRow:
    return UserRow(
        id=user.id.root,
        email=user.email.root,
        display_name=user.display_name.root,
        hashed_password=user.hashed_password.root,
    )


def session_from_row(row: SessionRow) -> Session:
    return Session(
        id=Id.model_validate(row.id),
        user_id=Id.model_validate(row.user_id),
        hashed_token=HashedSessionToken.model_validate(row.hashed_token),
        expires_at=row.expires_at,
    )


def session_to_row(session: Session) -> SessionRow:
    return SessionRow(
        id=session.id.root,
        user_id=session.user_id.root,
        hashed_token=session.hashed_token.root,
        expires_at=session.expires_at,
    )
