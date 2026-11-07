from rastro.auth.domain.aggregates import IssuedResetToken, Session, User
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    HashedResetToken,
    HashedSessionToken,
)
from rastro.auth.infrastructure.models import ResetTokenRow, SessionRow, UserRow
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


def reset_token_from_row(row: ResetTokenRow) -> IssuedResetToken:
    return IssuedResetToken(
        id=Id.model_validate(row.id),
        user_id=Id.model_validate(row.user_id),
        hashed_token=HashedResetToken.model_validate(row.hashed_token),
        issued_at=row.issued_at,
        expires_at=row.expires_at,
    )


def reset_token_to_row(reset_token: IssuedResetToken) -> ResetTokenRow:
    return ResetTokenRow(
        id=reset_token.id.root,
        user_id=reset_token.user_id.root,
        hashed_token=reset_token.hashed_token.root,
        issued_at=reset_token.issued_at,
        expires_at=reset_token.expires_at,
    )
