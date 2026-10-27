from typing import Protocol

from rastro.common.domain.value_objects import Id
from rastro.common.tests.sample.domain.aggregates import Note


class NoteRepository(Protocol):
    async def next_id(self) -> Id: ...

    async def add(self, note: Note) -> None: ...

    async def get_by_id(self, id: Id) -> Note | None: ...
