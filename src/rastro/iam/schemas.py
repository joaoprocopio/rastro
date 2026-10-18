import pydantic

from rastro.iam.values import DisplayName, Email, RawPassword


class IdentityRegisterInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    email: Email
    display_name: DisplayName
    password: RawPassword


class SessionStartInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    email: Email
    password: RawPassword
