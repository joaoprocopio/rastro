import pytest

from rastro.common.domain.value_objects import Id
from rastro.common.tests.adapter import RepositoryKind
from rastro.common.tests.fakes import FakeNoteRepository
from rastro.common.tests.sample.domain.aggregates import Note
from rastro.common.tests.sample.domain.ports import NoteRepository
from rastro.common.tests.sample.domain.value_objects import Color
from rastro.common.tests.sample.infrastructure.repositories import SqlNoteRepository


@pytest.fixture
def notes(adapter: RepositoryKind, request: pytest.FixtureRequest) -> NoteRepository:
    def sql() -> NoteRepository:
        request.getfixturevalue("sample_tables")
        return SqlNoteRepository(request.getfixturevalue("db_session"))

    return adapter.pick(fake=FakeNoteRepository, sql=sql)


@pytest.fixture
def read_notes(
    adapter: RepositoryKind, notes: NoteRepository, request: pytest.FixtureRequest
) -> NoteRepository:
    """The repository that reads back what `notes` wrote."""
    return adapter.pick(
        fake=lambda: notes,
        sql=lambda: SqlNoteRepository(request.getfixturevalue("reader")),
    )


async def test_get_by_id_reads_back_every_field_that_add_wrote(
    notes: NoteRepository, read_notes: NoteRepository
) -> None:
    note = Note(id=await notes.next_id(), color=Color("red"))

    await notes.add(note)

    assert await read_notes.get_by_id(note.id) == note


async def test_get_by_id_answers_none_for_an_unknown_id(
    notes: NoteRepository,
) -> None:
    assert await notes.get_by_id(Id(1)) is None


async def test_two_next_id_calls_return_two_different_ids(
    notes: NoteRepository,
) -> None:
    first, second = await notes.next_id(), await notes.next_id()

    assert isinstance(first, Id)
    assert isinstance(second, Id)
    assert first != second


async def test_a_field_assigned_with_no_update_keeps_its_stored_value(
    notes: NoteRepository, read_notes: NoteRepository
) -> None:
    note = Note(id=await notes.next_id(), color=Color("red"))
    await notes.add(note)
    note.color = Color("blue")
    read = await read_notes.get_by_id(note.id)
    assert read is not None
    read.color = Color("green")

    stored = await read_notes.get_by_id(note.id)

    assert stored == Note(id=note.id, color=Color("red"))
