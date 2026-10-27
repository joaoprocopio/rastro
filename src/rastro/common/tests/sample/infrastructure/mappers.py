from rastro.common.domain.value_objects import Id
from rastro.common.tests.sample.domain.aggregates import Note
from rastro.common.tests.sample.domain.value_objects import Color
from rastro.common.tests.sample.infrastructure.models import NoteRow


def note_from_row(row: NoteRow) -> Note:
    return Note(id=Id.model_validate(row.id), color=Color.model_validate(row.color))


def note_to_row(note: Note) -> NoteRow:
    return NoteRow(id=note.id.root, color=note.color.root)
