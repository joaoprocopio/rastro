from pydantic import PositiveInt

from rastro.common.domain.schemas import RootSchema, Schema


class ValueObject(Schema):
    pass


class RootValueObject[T](RootSchema[T]):
    pass


class Id(RootValueObject[PositiveInt]):
    pass
