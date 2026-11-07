import secrets
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid

import aiosmtplib
import argon2

from rastro.auth.domain.errors import (
    EmailNoAnswerError,
    EmailRefusedError,
    EmailTemporaryError,
)
from rastro.auth.domain.ports import PasswordCheck
from rastro.auth.domain.value_objects import (
    HashedPassword,
    OutgoingEmail,
    RawPassword,
)
from rastro.settings import Settings, SmtpSecurity


# JSON can hold a lone surrogate, which only surrogatepass encodes, and the bytes of other text stay the same.
def _password_bytes(password: RawPassword) -> bytes:
    return password.root.get_secret_value().encode("utf-8", "surrogatepass")


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = argon2.PasswordHasher()
        self._fixed_hash = HashedPassword.model_validate(
            self._hasher.hash(secrets.token_urlsafe())
        )

    def hash(self, *, password: RawPassword) -> HashedPassword:
        return HashedPassword.model_validate(
            self._hasher.hash(_password_bytes(password))
        )

    def verify(
        self, *, password: RawPassword, hashed: HashedPassword | None
    ) -> PasswordCheck:
        # An unknown email checks against the fixed hash, so it takes as long.
        checked = self._fixed_hash if hashed is None else hashed
        # Any other argon2 error means a corrupted hash, so it answers 500.
        try:
            self._hasher.verify(checked.root, _password_bytes(password))
        except argon2.exceptions.VerifyMismatchError:
            return PasswordCheck(is_correct=False, new_hash=None)
        if hashed is None:
            return PasswordCheck(is_correct=False, new_hash=None)
        if self._hasher.check_needs_rehash(hashed.root):
            return PasswordCheck(is_correct=True, new_hash=self.hash(password=password))
        return PasswordCheck(is_correct=True, new_hash=None)


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def _reply_code(error: Exception) -> int | None:
    if isinstance(error, aiosmtplib.SMTPRecipientsRefused):
        # The message has one recipient.
        (refused,) = error.recipients
        return refused.code
    if isinstance(error, aiosmtplib.SMTPResponseException):
        return error.code
    return None


# SMTPConnectResponseError has a code and SMTPConnectTimeoutError is a SMTPTimeoutError, so the order matters.
def _port_error(error: aiosmtplib.SMTPException | ssl.SSLError) -> Exception:
    code = _reply_code(error)
    if code is not None and 400 <= code < 500:
        return EmailTemporaryError()
    if code is not None and 500 <= code < 600:
        return EmailRefusedError()
    # aiosmtplib wraps a failed TLS handshake on connect, but not a failed one of STARTTLS.
    if isinstance(error, aiosmtplib.SMTPConnectError | ssl.SSLError):
        return EmailTemporaryError()
    # A code outside 4xx and 5xx, such as the -1 of a malformed reply, says nothing about the send.
    if code is not None or isinstance(
        error, aiosmtplib.SMTPServerDisconnected | aiosmtplib.SMTPTimeoutError
    ):
        return EmailNoAnswerError()
    # What remains is a server with no STARTTLS or no usable AUTH, which a retry does not change.
    return EmailRefusedError()


class SmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send(self, email: OutgoingEmail) -> None:
        settings = self._settings
        sender = settings.smtp_sender.root
        password = settings.smtp_password
        message = EmailMessage()
        message["From"] = sender
        message["To"] = email.to.root
        message["Subject"] = email.subject
        message["Date"] = format_datetime(datetime.now(UTC))
        message["Message-ID"] = make_msgid(domain=sender.partition("@")[2])
        message.set_content(email.body.get_secret_value())
        try:
            # With start_tls=None, aiosmtplib falls back to plain text on a server with no STARTTLS.
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port.root,
                username=settings.smtp_user,
                password=None if password is None else password.get_secret_value(),
                use_tls=settings.smtp_security is SmtpSecurity.TLS,
                start_tls=settings.smtp_security is SmtpSecurity.STARTTLS,
                timeout=settings.smtp_timeout.total_seconds(),
            )
        except (aiosmtplib.SMTPException, ssl.SSLError) as error:
            raise _port_error(error) from error
