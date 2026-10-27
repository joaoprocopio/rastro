import pytest

from rastro.common.domain.value_objects import Id
from rastro.common.tests.fakes import FakeNoteRepository
from rastro.common.tests.sample.application.use_cases import note_create, note_reject
from rastro.common.tests.sample.domain.aggregates import Note
from rastro.common.tests.sample.domain.errors import NoteRejectedError
from rastro.common.tests.sample.domain.value_objects import Color


@pytest.fixture
def notes() -> FakeNoteRepository:
    return FakeNoteRepository()


async def test_note_create_adds_a_yellow_note_with_the_next_id(
    notes: FakeNoteRepository,
) -> None:
    await note_create(notes=notes)

    assert notes.notes == {Id(1): Note(id=Id(1), color=Color("yellow"))}


async def test_note_reject_raises_note_rejected_error(
    notes: FakeNoteRepository,
) -> None:
    with pytest.raises(NoteRejectedError):
        await note_reject(notes=notes)
