from rastro.common.domain.value_objects import Id
from rastro.common.tests.sample.domain.aggregates import Note


class FakeNoteRepository:
    def __init__(self) -> None:
        self.notes: dict[Id, Note] = {}
        self._last_id = 0

    async def next_id(self) -> Id:
        self._last_id += 1
        return Id(self._last_id)

    async def add(self, note: Note) -> None:
        self.notes[note.id] = note.model_copy()

    async def get_by_id(self, id: Id) -> Note | None:
        note = self.notes.get(id)
        return None if note is None else note.model_copy()
