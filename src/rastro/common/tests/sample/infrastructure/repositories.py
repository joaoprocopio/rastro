from sqlalchemy.ext.asyncio import AsyncSession

from rastro.common.domain.value_objects import Id
from rastro.common.infrastructure.repositories import next_id
from rastro.common.tests.sample.domain.aggregates import Note
from rastro.common.tests.sample.infrastructure.mappers import note_from_row, note_to_row
from rastro.common.tests.sample.infrastructure.models import NoteRow


class SqlNoteRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def next_id(self) -> Id:
        return await next_id(self._db_session, column=NoteRow.id)

    async def add(self, note: Note) -> None:
        self._db_session.add(note_to_row(note))
        # A constraint violation rises here, inside add.
        await self._db_session.flush()

    async def get_by_id(self, id: Id) -> Note | None:
        row = await self._db_session.get(NoteRow, id.root)
        return None if row is None else note_from_row(row)
