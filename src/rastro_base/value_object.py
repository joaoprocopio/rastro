from typing import TypeVar

from pydantic import ConfigDict

from rastro_base.pydantic import BaseModel, RootModel

T = TypeVar("T")


class RootValueObject(RootModel[T]):
    model_config = ConfigDict(frozen=True)


class ValueObject(BaseModel):
    model_config = ConfigDict(frozen=True)
