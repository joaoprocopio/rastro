from abc import ABC
from dataclasses import dataclass
from typing import Generic, TypeVar, cast

from rastro.base.aggregate import Aggregate
from rastro_base.error import InvalidIdError
from rastro_base.value_object import ValueObject


class Id(ValueObject[int]):
    def validate(self) -> None:
        if self.value < 1:
            raise InvalidIdError()


ID = TypeVar("ID")


@dataclass
class Entity(Aggregate, Generic[ID], ABC):
    id: ID

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented

        other_entity: Entity[ID] = cast(Entity[ID], other)
        return self.id == other_entity.id

    def __hash__(self) -> int:
        return hash(self.id)
