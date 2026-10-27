from collections.abc import AsyncIterator

import pydantic
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rastro.common.domain.value_objects import Id
from rastro.common.tests.sample.domain.aggregates import Note
from rastro.common.tests.sample.domain.value_objects import Color
from rastro.common.tests.sample.infrastructure.models import NoteRow
from rastro.common.tests.sample.infrastructure.repositories import SqlNoteRepository

pytestmark = pytest.mark.usefixtures("sample_tables")


@pytest.fixture
async def db_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as db_session:
        yield db_session


async def test_get_by_id_reads_back_every_field_that_add_wrote(
    db_session: AsyncSession, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    notes = SqlNoteRepository(db_session)
    note = Note(id=await notes.next_id(), color=Color("red"))

    await notes.add(note)

    # A second session reads the row from the database, not from the first's cache.
    async with sessionmaker() as reader:
        assert await SqlNoteRepository(reader).get_by_id(note.id) == note


async def test_get_by_id_answers_none_for_an_unknown_id(
    db_session: AsyncSession,
) -> None:
    assert await SqlNoteRepository(db_session).get_by_id(Id(1)) is None


async def test_two_next_id_calls_return_two_different_ids(
    db_session: AsyncSession,
) -> None:
    notes = SqlNoteRepository(db_session)

    first, second = await notes.next_id(), await notes.next_id()

    assert isinstance(first, Id)
    assert isinstance(second, Id)
    assert first != second


async def test_a_row_that_breaks_its_value_object_fails_to_become_an_aggregate(
    db_session: AsyncSession,
) -> None:
    db_session.add(NoteRow(id=1, color="Green"))
    await db_session.flush()

    with pytest.raises(pydantic.ValidationError):
        await SqlNoteRepository(db_session).get_by_id(Id(1))
