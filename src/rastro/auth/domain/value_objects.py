import hashlib
import secrets
import unicodedata
from datetime import timedelta
from typing import Annotated, Self

from pydantic import BeforeValidator, Field, SecretStr, StringConstraints

from rastro.common.domain.value_objects import RootValueObject, TokenBytes

EMAIL_PATTERN = r"^[a-z0-9_.+-]+@[a-z0-9-]+\.[a-z0-9-.]+$"
EMAIL_MAX_LENGTH = 254
DISPLAY_NAME_MAX_LENGTH = 320
RAW_PASSWORD_MIN_LENGTH = 8

SessionLifetime = Annotated[timedelta, Field(gt=timedelta(0))]


def _nfkc(value: object) -> object:
    return unicodedata.normalize("NFKC", value) if isinstance(value, str) else value


class Email(
    RootValueObject[
        Annotated[
            str,
            BeforeValidator(_nfkc),
            StringConstraints(
                strip_whitespace=True,
                to_lower=True,
                max_length=EMAIL_MAX_LENGTH,
                pattern=EMAIL_PATTERN,
            ),
        ]
    ]
):
    pass


class DisplayName(
    RootValueObject[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True, max_length=DISPLAY_NAME_MAX_LENGTH
            ),
        ]
    ]
):
    pass


class RawPassword(
    RootValueObject[
        Annotated[SecretStr, StringConstraints(min_length=RAW_PASSWORD_MIN_LENGTH)]
    ]
):
    pass


class HashedPassword(RootValueObject[str]):
    pass


# The SHA-256 digest of a Session token, so a leaked database starts no Session.
class HashedSessionToken(RootValueObject[bytes]):
    pass


class SessionToken(RootValueObject[SecretStr]):
    @classmethod
    def generate(cls, *, nbytes: TokenBytes) -> Self:
        return cls(SecretStr(secrets.token_urlsafe(nbytes)))

    def digest(self) -> HashedSessionToken:
        value = self.root.get_secret_value().encode()
        return HashedSessionToken(hashlib.sha256(value).digest())
