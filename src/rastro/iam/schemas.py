import pydantic

from rastro.iam.values import DisplayName, Email, RawPassword


class SessionStartInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    email: Email
    password: RawPassword


class SessionCurrentOutput(pydantic.BaseModel):
    email: Email
    display_name: DisplayName
