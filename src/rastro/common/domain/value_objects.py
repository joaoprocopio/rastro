import secrets
from typing import Annotated, Self

from pydantic import Field, PositiveInt, SecretStr

from rastro.common.domain.schemas import RootSchema, Schema

# A token shorter than 16 random bytes is short enough to guess.
TokenBytes = Annotated[int, Field(ge=16)]


class ValueObject(Schema):
    pass


class RootValueObject[T](RootSchema[T]):
    pass


class Id(RootValueObject[PositiveInt]):
    pass


class CsrfToken(RootValueObject[SecretStr]):
    @classmethod
    def generate(cls, *, nbytes: TokenBytes) -> Self:
        return cls(SecretStr(secrets.token_urlsafe(nbytes)))

    def matches(self, other: CsrfToken) -> bool:
        return secrets.compare_digest(
            self.root.get_secret_value().encode(),
            other.root.get_secret_value().encode(),
        )
