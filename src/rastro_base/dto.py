from pydantic import ConfigDict

from rastro_base.pydantic import BaseModel


class DTO(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )
