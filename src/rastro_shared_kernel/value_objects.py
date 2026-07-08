from pydantic import PositiveInt

from rastro_base.value_object import RootValueObject


class Id(RootValueObject[PositiveInt]):
    pass
