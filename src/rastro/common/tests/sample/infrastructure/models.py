from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, MetaData, String, func
from sqlalchemy.orm import Mapped, mapped_column

from rastro.common.infrastructure.models import Row


# Its own metadata keeps the sample rows out of the metadata that Alembic migrates.
class SampleRow(Row):
    __abstract__ = True
    metadata = MetaData()


class NoteRow(SampleRow):
    __tablename__ = "common_sample_note"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    color: Mapped[str] = mapped_column(String(6))
