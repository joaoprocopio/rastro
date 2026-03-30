from abc import ABC
from dataclasses import dataclass
from typing import Generic, TypeVar, cast

from rastro.base.errors import InvalidIdError
from rastro.base.value_objects import ValueObject

ID = TypeVar("ID")


@dataclass
class Entity(ABC, Generic[ID]):
    id: ID | None

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented

        other_entity: Entity[ID] = cast(Entity[ID], other)

        if self.id is None or other_entity.id is None:
            return self is other

        return self.id == other_entity.id


class Id(ValueObject[int]):
    def validate(self) -> None:
        if not self.value >= 1:
            raise InvalidIdError()
