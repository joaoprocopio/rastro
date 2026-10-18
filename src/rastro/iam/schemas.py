import pydantic

from rastro.iam.values import Email, RawPassword


class SessionStartInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    email: Email
    password: RawPassword
