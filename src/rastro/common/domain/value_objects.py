import secrets
from typing import Self

from pydantic import PositiveInt, SecretStr

from rastro.common.domain.schemas import RootSchema, Schema


class ValueObject(Schema):
    pass


class RootValueObject[T](RootSchema[T]):
    pass


class Id(RootValueObject[PositiveInt]):
    pass


class TokenValueObject(RootValueObject[SecretStr]):
    @classmethod
    def generate(cls, *, nbytes: int) -> Self:
        return cls(SecretStr(secrets.token_urlsafe(nbytes)))


class CsrfToken(TokenValueObject):
    pass
