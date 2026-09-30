from pydantic import BaseModel, ConfigDict


class RastroBase(BaseModel):
    """Base for every request and response schema.

    `strict` turns off type coercion, so `"1"` does not validate as `1`, and
    `extra="forbid"` rejects unknown keys in a request body. Each string type
    states its own whitespace stripping, because a password keeps its spaces.
    """

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        from_attributes=True,
    )
