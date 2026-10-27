from rastro.common.tests.sample.domain.aggregates import Note
from rastro.common.tests.sample.domain.errors import NoteRejectedError
from rastro.common.tests.sample.domain.ports import NoteRepository
from rastro.common.tests.sample.domain.value_objects import Color

NEW_NOTE_COLOR = Color("yellow")


async def note_create(*, notes: NoteRepository) -> None:
    await notes.add(Note(id=await notes.next_id(), color=NEW_NOTE_COLOR))


async def note_reject(*, notes: NoteRepository) -> None:
    await note_create(notes=notes)
    raise NoteRejectedError()
