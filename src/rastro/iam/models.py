from datetime import datetime
from typing import Annotated

import sqlalchemy as sa
from pydantic import Field, SecretStr, StringConstraints
from sqlalchemy.orm import Mapped, mapped_column

from rastro.database.core import Base
from rastro.models import RastroBase

# https://emailregex.com/
EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
# RFC 5321 limits a forward path to 256 octets, and the two angle brackets
# leave 254 for the address.
EMAIL_MAX_LENGTH = 254
DISPLAY_NAME_MAX_LENGTH = 320

Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        max_length=EMAIL_MAX_LENGTH,
        pattern=EMAIL_PATTERN,
    ),
]
DisplayName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=DISPLAY_NAME_MAX_LENGTH),
]
# `SecretStr` keeps the password out of `repr()` and logs. The password keeps its
# leading and trailing whitespace, so it matches what the person typed. The
# upper bound follows OWASP: long enough for a passphrase, short enough that
# hashing it cannot tie up a worker.
Password = Annotated[SecretStr, Field(min_length=8, max_length=128)]


class Identity(Base):
    """The authenticated principal: who signs in, and with which credentials."""

    __tablename__ = "iam_identity"

    id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.Identity(always=True), primary_key=True, init=False
    )
    email: Mapped[str] = mapped_column(sa.String(EMAIL_MAX_LENGTH), unique=True)
    password_hash: Mapped[str] = mapped_column(sa.Text, repr=False)
    display_name: Mapped[str] = mapped_column(sa.String(DISPLAY_NAME_MAX_LENGTH))
    date_joined: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), init=False
    )
    last_login: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), default=None
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.true(), default=True
    )


class IdentityRegister(RastroBase):
    display_name: DisplayName
    email: Email
    password: Password


class IdentityAuthenticate(RastroBase):
    email: Email
    password: Password


class IdentityRead(RastroBase):
    """The public projection of an `Identity`, the only one that leaves the API."""

    display_name: str
    email: str
