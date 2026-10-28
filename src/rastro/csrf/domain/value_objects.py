import secrets
from typing import Self

from pydantic import SecretStr

from rastro.common.domain.value_objects import RootValueObject, TokenBytes


class CsrfToken(RootValueObject[SecretStr]):
    @classmethod
    def generate(cls, *, nbytes: TokenBytes) -> Self:
        return cls(SecretStr(secrets.token_urlsafe(nbytes.root)))

    def matches(self, other: CsrfToken) -> bool:
        return secrets.compare_digest(
            self.root.get_secret_value().encode(),
            other.root.get_secret_value().encode(),
        )
