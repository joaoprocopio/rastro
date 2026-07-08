from typing import Generic, TypeVar

import pydantic

T = TypeVar("T")


class RootModel(pydantic.RootModel[T], Generic[T]):
    model_config = pydantic.ConfigDict(
        str_strip_whitespace=True,
    )


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )
