from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rastro.common.infrastructure.models import Row

ID = "id"


async def next_id(db_session: AsyncSession, row_class: type[Row]) -> int:
    sequence = func.pg_get_serial_sequence(row_class.__tablename__, ID)
    next_id = await db_session.scalar(select(func.nextval(sequence)))
    if next_id is None:
        raise RuntimeError("nextval returned no row.")
    return int(next_id)


async def existing_row[R: Row](
    db_session: AsyncSession, row_class: type[R], id: int
) -> R:
    row = await db_session.get(row_class, id)
    if row is None:
        raise LookupError(f"No {row_class.__name__} with the id {id}.")
    return row
