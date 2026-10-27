from rastro.common.tests.sample.domain.aggregates import Note


class FakeNoteRepository:
    def __init__(self) -> None:
        self.notes: dict[int, Note] = {}
        self._last_id = 0

    async def next_id(self) -> int:
        self._last_id += 1
        return self._last_id

    async def add(self, note: Note) -> None:
        self.notes[note.id] = note

    async def get_by_id(self, id: int) -> Note | None:
        return self.notes.get(id)
