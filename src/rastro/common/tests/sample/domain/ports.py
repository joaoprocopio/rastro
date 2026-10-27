from typing import Protocol

from rastro.common.tests.sample.domain.aggregates import Note


class NoteRepository(Protocol):
    async def next_id(self) -> int: ...

    async def add(self, note: Note) -> None: ...

    async def get_by_id(self, id: int) -> Note | None: ...
