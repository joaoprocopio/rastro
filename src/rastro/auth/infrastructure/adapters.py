import secrets
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid

import aiosmtplib
import argon2

from rastro.auth.domain.ports import PasswordCheck
from rastro.auth.domain.value_objects import (
    HashedPassword,
    OutgoingEmail,
    RawPassword,
)
from rastro.settings import Settings, SmtpSecurity


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = argon2.PasswordHasher()
        self._fixed_hash = HashedPassword.model_validate(
            self._hasher.hash(secrets.token_urlsafe())
        )

    def hash(self, *, password: RawPassword) -> HashedPassword:
        return HashedPassword.model_validate(
            self._hasher.hash(password.root.get_secret_value())
        )

    def verify(
        self, *, password: RawPassword, hashed: HashedPassword | None
    ) -> PasswordCheck:
        # An unknown email checks against the fixed hash, so it takes as long.
        checked = self._fixed_hash if hashed is None else hashed
        # Any other argon2 error means a corrupted hash, so it answers 500.
        try:
            self._hasher.verify(checked.root, password.root.get_secret_value())
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
        # With start_tls=None, aiosmtplib falls back to plain text on a server with no STARTTLS.
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=None if password is None else password.get_secret_value(),
            use_tls=settings.smtp_security is SmtpSecurity.TLS,
            start_tls=settings.smtp_security is SmtpSecurity.STARTTLS,
        )
