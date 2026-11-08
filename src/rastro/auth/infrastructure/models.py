from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    LargeBinary,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from rastro.auth.domain.value_objects import DISPLAY_NAME_MAX_LENGTH, EMAIL_MAX_LENGTH
from rastro.common.infrastructure.models import Row

USER_EMAIL_KEY = "auth_user_email_key"
RESET_TOKEN_USER_KEY = "auth_reset_token_user_id_key"


class UserRow(Row):
    __tablename__ = "auth_user"
    __table_args__ = (UniqueConstraint("email", name=USER_EMAIL_KEY),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH))
    display_name: Mapped[str] = mapped_column(String(DISPLAY_NAME_MAX_LENGTH))
    hashed_password: Mapped[str] = mapped_column(String)


class SessionRow(Row):
    __tablename__ = "auth_session"
    __table_args__ = (
        UniqueConstraint("hashed_token", name="auth_session_hashed_token_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(UserRow.id, ondelete="CASCADE"), index=True
    )
    # The SHA-256 digest of the token, so a leaked database starts no Session.
    hashed_token: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ResetTokenRow(Row):
    __tablename__ = "auth_reset_token"
    __table_args__ = (
        UniqueConstraint("user_id", name=RESET_TOKEN_USER_KEY),
        UniqueConstraint("hashed_token", name="auth_reset_token_hashed_token_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    # The unique constraint already indexes this column.
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(UserRow.id, ondelete="CASCADE")
    )
    # The SHA-256 digest of the token, so a leaked database changes no password.
    hashed_token: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
