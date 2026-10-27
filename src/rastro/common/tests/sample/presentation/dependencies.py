from rastro.common.presentation.dependencies import DatabaseSession
from rastro.common.tests.sample.domain.ports import NoteRepository
from rastro.common.tests.sample.infrastructure.repositories import SqlNoteRepository


def note_repository(db_session: DatabaseSession) -> NoteRepository:
    return SqlNoteRepository(db_session)
