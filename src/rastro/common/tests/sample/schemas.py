import pydantic

from rastro.common.tests.sample.values import Color


class PaintApplyInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    color: Color
    coats: int


class PaintApplyOutput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    color: Color
    coats: int
