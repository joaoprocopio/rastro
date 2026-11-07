from sqlalchemy import Column, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from rastro.common.domain.value_objects import Id
from rastro.common.infrastructure.models import Row


async def next_id(
    db_session: AsyncSession, *, column: InstrumentedAttribute[int]
) -> Id:
    table_column = column.expression
    if not isinstance(table_column, Column):
        raise TypeError(f"{column} maps no table column.")
    sequence = func.pg_get_serial_sequence(
        table_column.table.fullname, table_column.name
    )
    next_id = await db_session.scalar(select(func.nextval(sequence)))
    if next_id is None:
        raise RuntimeError("nextval returned no row.")
    return Id(next_id)


async def existing_row[R: Row](
    db_session: AsyncSession, row_class: type[R], id: Id
) -> R:
    row = await db_session.get(row_class, id.root)
    if row is None:
        raise LookupError(f"No {row_class.__name__} with the id {id.root}.")
    return row
