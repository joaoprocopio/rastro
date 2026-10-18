from pydantic import ConfigDict

from rastro_base.pydantic import BaseModel


class DTO(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        # The value objects normalize their own value, and a password keeps its spaces.
        str_strip_whitespace=False,
    )
