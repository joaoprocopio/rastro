from pydantic import BaseModel, ConfigDict, RootModel


class Schema(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        from_attributes=True,
        extra="forbid",
        hide_input_in_errors=True,
    )


# Pydantic rejects extra on a RootModel.
class RootSchema[T](RootModel[T]):
    model_config = ConfigDict(frozen=True, strict=True, hide_input_in_errors=True)
