from datetime import timedelta

import aiosmtplib
import argon2
import pytest
from pydantic import SecretStr

from rastro.auth.domain.ports import PasswordCheck
from rastro.auth.domain.value_objects import (
    Email,
    HashedPassword,
    OutgoingEmail,
    RawPassword,
    ResetLinkUrl,
    ResetToken,
    ResetTokenLifetime,
)
from rastro.auth.infrastructure.adapters import Argon2PasswordHasher, SmtpEmailSender
from rastro.auth.tests.conftest import SmtpRecorder
from rastro.settings import Settings, SmtpSecurity

PASSWORD = RawPassword(SecretStr("password"))
TOKEN = "a-token-longer-than-the-78-columns-that-email-allows-before-it-folds-a-line"
EMAIL = OutgoingEmail.password_reset(
    to=Email("ana@x.com"),
    link_url=ResetLinkUrl("https://rastro.example/password-reset"),
    token=ResetToken(SecretStr(TOKEN)),
    lifetime=ResetTokenLifetime(timedelta(hours=1)),
)


def test_argon2_accepts_the_password_of_a_current_hash() -> None:
    hasher = Argon2PasswordHasher()

    check = hasher.verify(password=PASSWORD, hashed=hasher.hash(password=PASSWORD))

    assert check == PasswordCheck(is_correct=True, new_hash=None)


def test_argon2_rejects_a_wrong_password() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash(password=RawPassword(SecretStr("otherpassword")))

    assert hasher.verify(password=PASSWORD, hashed=hashed) == PasswordCheck(
        is_correct=False, new_hash=None
    )


def test_argon2_rejects_any_password_with_no_hash() -> None:
    assert Argon2PasswordHasher().verify(
        password=PASSWORD, hashed=None
    ) == PasswordCheck(is_correct=False, new_hash=None)


def test_argon2_returns_a_current_hash_for_an_outdated_one() -> None:
    hasher = Argon2PasswordHasher()
    outdated = HashedPassword(
        argon2.PasswordHasher(time_cost=1).hash(PASSWORD.root.get_secret_value())
    )

    check = hasher.verify(password=PASSWORD, hashed=outdated)

    assert check.is_correct
    assert check.new_hash is not None
    assert hasher.verify(password=PASSWORD, hashed=check.new_hash) == PasswordCheck(
        is_correct=True, new_hash=None
    )


async def test_smtp_sends_a_plain_text_email_from_the_configured_sender(
    smtp_settings: Settings, smtp_recorder: SmtpRecorder
) -> None:
    await SmtpEmailSender(smtp_settings).send(EMAIL)

    (message,) = smtp_recorder.messages
    assert message["From"] == "no-reply@rastro.example"
    assert message["To"] == "ana@x.com"
    assert message["Subject"] == "Reset your rastro password"
    assert message["Date"] is not None
    assert message["Message-ID"].endswith("@rastro.example>")
    assert message.get_content_type() == "text/plain"
    assert message.get_content().splitlines() == (
        EMAIL.body.get_secret_value().splitlines()
    )


async def test_smtp_keeps_the_link_whole_through_the_transfer_encoding(
    smtp_settings: Settings, smtp_recorder: SmtpRecorder
) -> None:
    await SmtpEmailSender(smtp_settings).send(EMAIL)

    (message,) = smtp_recorder.messages
    link = f"https://rastro.example/password-reset#token={TOKEN}"
    assert link in message.get_content().splitlines()


async def test_smtp_sends_no_login_with_no_user(
    smtp_settings: Settings, smtp_recorder: SmtpRecorder
) -> None:
    await SmtpEmailSender(smtp_settings).send(EMAIL)

    assert smtp_recorder.logins == []


async def test_smtp_logs_in_with_the_configured_user_and_password(
    smtp_settings: Settings, smtp_recorder: SmtpRecorder
) -> None:
    settings = smtp_settings.model_copy(
        update={"smtp_user": "ana", "smtp_password": SecretStr("hunter2")}
    )

    await SmtpEmailSender(settings).send(EMAIL)

    assert smtp_recorder.logins == [("ana", "hunter2")]
    assert len(smtp_recorder.messages) == 1


async def test_starttls_on_a_server_with_no_starttls_sends_no_plain_text(
    smtp_settings: Settings, smtp_recorder: SmtpRecorder
) -> None:
    settings = smtp_settings.model_copy(update={"smtp_security": SmtpSecurity.STARTTLS})

    with pytest.raises(aiosmtplib.SMTPException, match="STARTTLS"):
        await SmtpEmailSender(settings).send(EMAIL)

    assert smtp_recorder.messages == []


async def test_tls_on_a_server_with_no_tls_sends_no_plain_text(
    smtp_settings: Settings, smtp_recorder: SmtpRecorder
) -> None:
    settings = smtp_settings.model_copy(update={"smtp_security": SmtpSecurity.TLS})

    with pytest.raises(aiosmtplib.SMTPException):
        await SmtpEmailSender(settings).send(EMAIL)

    assert smtp_recorder.messages == []
