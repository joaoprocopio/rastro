import hashlib
import secrets
import unicodedata
from datetime import timedelta
from typing import Annotated, Self

from pydantic import BeforeValidator, Field, SecretStr, StringConstraints

from rastro.common.domain.value_objects import (
    RootValueObject,
    TokenBytes,
    ValueObject,
)

EMAIL_PATTERN = r"^[a-z0-9_.+-]+@[a-z0-9-]+\.[a-z0-9-.]+$"
EMAIL_MAX_LENGTH = 254
DISPLAY_NAME_MAX_LENGTH = 320
RAW_PASSWORD_MIN_LENGTH = 8
# The token goes into the fragment, so a fragment of the setting would break the link.
RESET_LINK_URL_PATTERN = r"^https?://[^#\s]+$"


def _nfkc(value: object) -> object:
    return unicodedata.normalize("NFKC", value) if isinstance(value, str) else value


def _counted(count: int, *, unit: str) -> str:
    return f"{count} {unit}" if count == 1 else f"{count} {unit}s"


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


class SessionLifetime(
    RootValueObject[Annotated[timedelta, Field(gt=timedelta(0), strict=False)]]
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
        return cls(SecretStr(secrets.token_urlsafe(nbytes.root)))

    def digest(self) -> HashedSessionToken:
        value = self.root.get_secret_value().encode()
        return HashedSessionToken(hashlib.sha256(value).digest())


class ResetTokenLifetime(
    RootValueObject[Annotated[timedelta, Field(gt=timedelta(0), strict=False)]]
):
    def in_words(self) -> str:
        seconds = int(self.root.total_seconds())
        if seconds % 3600 == 0:
            return _counted(seconds // 3600, unit="hour")
        if seconds % 60 == 0:
            return _counted(seconds // 60, unit="minute")
        return _counted(seconds, unit="second")


class ResetTokenCooldown(
    RootValueObject[Annotated[timedelta, Field(gt=timedelta(0), strict=False)]]
):
    pass


class ResetLinkUrl(
    RootValueObject[Annotated[str, StringConstraints(pattern=RESET_LINK_URL_PATTERN)]]
):
    pass


# The SHA-256 digest of a Reset token, so a leaked database changes no password.
class HashedResetToken(RootValueObject[bytes]):
    pass


class ResetToken(RootValueObject[SecretStr]):
    @classmethod
    def generate(cls, *, nbytes: TokenBytes) -> Self:
        return cls(SecretStr(secrets.token_urlsafe(nbytes.root)))

    def digest(self) -> HashedResetToken:
        # JSON can hold a lone surrogate, and such a token is one more unknown token.
        value = self.root.get_secret_value().encode(errors="surrogatepass")
        return HashedResetToken(hashlib.sha256(value).digest())


class OutgoingEmail(ValueObject):
    to: Email
    subject: str
    # A body can hold a link that lets its holder act.
    body: SecretStr

    @classmethod
    def password_reset(
        cls,
        *,
        to: Email,
        link_url: ResetLinkUrl,
        token: ResetToken,
        lifetime: ResetTokenLifetime,
    ) -> Self:
        # A browser never sends the fragment, so the token stays out of access logs.
        link = f"{link_url.root}#token={token.root.get_secret_value()}"
        return cls(
            to=to,
            subject="Reset your rastro password",
            body=SecretStr(
                "Someone asked to reset your rastro password.\n\n"
                "To choose a new password, open this link. "
                f"The link works for {lifetime.in_words()} and only once:\n\n"
                f"{link}\n\n"
                "If you did not ask for this, ignore this email. "
                "Your password stays the same.\n"
            ),
        )
