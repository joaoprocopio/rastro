from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rastro.database.core import Base
from rastro.iam.models import Identity


class IdentitySession(Base):
    """A server-side session, started when an `Identity` signs in.

    The table stores the SHA-256 digest of the session token, never the token.
    A read of the table then does not yield a cookie that signs anyone in.
    """

    __tablename__ = "iam_session"

    id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.Identity(always=True), primary_key=True, init=False
    )
    token_digest: Mapped[bytes] = mapped_column(
        sa.LargeBinary(32), unique=True, repr=False
    )
    identity_id: Mapped[int] = mapped_column(
        sa.BigInteger,
        sa.ForeignKey(Identity.id, ondelete="CASCADE"),
        index=True,
        init=False,
    )
    # `lazy="raise"` turns an implicit lazy load into an error, so every query
    # states the relationships it loads and no N+1 query slips in.
    identity: Mapped[Identity] = relationship(lazy="raise")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
