import socket
from datetime import timedelta

import argon2
import pytest
from pydantic import SecretStr

from rastro.auth.domain.errors import (
    EmailNoAnswerError,
    EmailRefusedError,
    EmailTemporaryError,
)
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
from rastro.auth.tests.conftest import SmtpFault, SmtpRecorder, SmtpScript
from rastro.settings import Settings, SmtpPort, SmtpSecurity, SmtpTimeout

PASSWORD = RawPassword(SecretStr("password"))
LONE_SURROGATE_PASSWORD = RawPassword(SecretStr("\ud800aaaaaaaa"))
TOKEN = "a-token-longer-than-the-78-columns-that-email-allows-before-it-folds-a-line"
SHORT_TIMEOUT = SmtpTimeout(timedelta(milliseconds=250))
# Argon2PasswordHasher made these two when it passed argon2 the str of the password.
ASCII_HASH_MADE_FROM_A_STR = (
    "$argon2id$v=19$m=65536,t=3,p=4$uoa+XKroLFsFNBQVI5GLrg"
    "$LEZ+EsUgBuj++oZox1+lnyTOlMaQi69Gna8b4ZZ0LBQ"
)
UTF8_HASH_MADE_FROM_A_STR = (
    "$argon2id$v=19$m=65536,t=3,p=4$znHMOkhin34/LjEeFrgmbA"
    "$Ip/uVO+q8Us/ISrE7pcUpgVdPZiX7FpTKZjH94bKGWU"
)
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


def test_argon2_accepts_a_password_with_a_lone_surrogate() -> None:
    hasher = Argon2PasswordHasher()

    check = hasher.verify(
        password=LONE_SURROGATE_PASSWORD,
        hashed=hasher.hash(password=LONE_SURROGATE_PASSWORD),
    )

    assert check == PasswordCheck(is_correct=True, new_hash=None)


@pytest.mark.parametrize(
    "wrong", ["\ud801aaaaaaaa", "\ud800aaaaaaab", "aaaaaaaaa"], ids=repr
)
def test_argon2_rejects_a_wrong_password_for_a_password_with_a_lone_surrogate(
    wrong: str,
) -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash(password=LONE_SURROGATE_PASSWORD)

    check = hasher.verify(password=RawPassword(SecretStr(wrong)), hashed=hashed)

    assert check == PasswordCheck(is_correct=False, new_hash=None)


def test_argon2_rejects_a_lone_surrogate_with_no_hash() -> None:
    assert Argon2PasswordHasher().verify(
        password=LONE_SURROGATE_PASSWORD, hashed=None
    ) == PasswordCheck(is_correct=False, new_hash=None)


@pytest.mark.parametrize(
    ("password", "stored"),
    [
        pytest.param("password", ASCII_HASH_MADE_FROM_A_STR, id="ascii"),
        pytest.param("s\xe9nha-\U0001f600-\xa5", UTF8_HASH_MADE_FROM_A_STR, id="utf_8"),
    ],
)
def test_argon2_verifies_a_hash_that_it_made_from_a_str_before_it_hashed_bytes(
    password: str, stored: str
) -> None:
    check = Argon2PasswordHasher().verify(
        password=RawPassword(SecretStr(password)), hashed=HashedPassword(stored)
    )

    assert check.is_correct


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

    with pytest.raises(EmailRefusedError):
        await SmtpEmailSender(settings).send(EMAIL)

    assert smtp_recorder.messages == []


async def test_tls_on_a_server_with_no_tls_sends_no_plain_text(
    smtp_settings: Settings, smtp_recorder: SmtpRecorder
) -> None:
    settings = smtp_settings.model_copy(update={"smtp_security": SmtpSecurity.TLS})

    with pytest.raises(EmailTemporaryError):
        await SmtpEmailSender(settings).send(EMAIL)

    assert smtp_recorder.messages == []


@pytest.mark.parametrize(
    ("replies", "error"),
    [
        pytest.param({"MAIL": "451 Later"}, EmailTemporaryError, id="sender-4xx"),
        pytest.param({"MAIL": "550 No"}, EmailRefusedError, id="sender-5xx"),
        pytest.param({"DATA": "451 Later"}, EmailTemporaryError, id="data-4xx"),
        pytest.param({"DATA": "554 No"}, EmailRefusedError, id="data-5xx"),
        pytest.param({"BODY": "451 Later"}, EmailTemporaryError, id="body-4xx"),
        pytest.param({"BODY": "554 No"}, EmailRefusedError, id="body-5xx"),
        pytest.param({"RCPT": "450 Later"}, EmailTemporaryError, id="recipient-4xx"),
        pytest.param({"RCPT": "550 No"}, EmailRefusedError, id="recipient-5xx"),
        pytest.param({"EHLO": "421 Later"}, EmailTemporaryError, id="hello-4xx-closes"),
        pytest.param(
            {"EHLO": "550 No", "HELO": "550 No"}, EmailRefusedError, id="hello-5xx"
        ),
        pytest.param({"GREETING": "421 Later"}, EmailTemporaryError, id="greeting-4xx"),
        pytest.param({"GREETING": "554 No"}, EmailRefusedError, id="greeting-5xx"),
    ],
)
async def test_a_reply_of_the_server_raises_the_error_of_its_class(
    scripted_smtp_settings: Settings,
    smtp_script: SmtpScript,
    replies: dict[str, str],
    error: type[Exception],
) -> None:
    smtp_script.replies.update(replies)

    with pytest.raises(error):
        await SmtpEmailSender(scripted_smtp_settings).send(EMAIL)


@pytest.mark.parametrize("step", ["EHLO", "MAIL", "RCPT", "DATA", "BODY"])
async def test_a_connection_lost_after_it_opens_is_no_answer(
    scripted_smtp_settings: Settings, smtp_script: SmtpScript, step: str
) -> None:
    smtp_script.replies[step] = SmtpFault.CLOSE

    with pytest.raises(EmailNoAnswerError):
        await SmtpEmailSender(scripted_smtp_settings).send(EMAIL)


async def test_a_connection_lost_before_the_greeting_is_a_temporary_failure(
    scripted_smtp_settings: Settings, smtp_script: SmtpScript
) -> None:
    smtp_script.replies["GREETING"] = SmtpFault.CLOSE

    with pytest.raises(EmailTemporaryError):
        await SmtpEmailSender(scripted_smtp_settings).send(EMAIL)


async def test_a_port_that_refuses_the_connection_is_a_temporary_failure(
    scripted_smtp_settings: Settings,
) -> None:
    # A socket that is bound and does not listen keeps its port and refuses a connection.
    with socket.socket() as closed:
        closed.bind(("127.0.0.1", 0))
        settings = scripted_smtp_settings.model_copy(
            update={"smtp_port": SmtpPort(closed.getsockname()[1])}
        )

        with pytest.raises(EmailTemporaryError):
            await SmtpEmailSender(settings).send(EMAIL)


@pytest.mark.parametrize("step", ["EHLO", "MAIL", "RCPT", "DATA", "BODY"])
async def test_a_silent_server_after_the_greeting_is_no_answer(
    scripted_smtp_settings: Settings, smtp_script: SmtpScript, step: str
) -> None:
    settings = scripted_smtp_settings.model_copy(update={"smtp_timeout": SHORT_TIMEOUT})
    smtp_script.replies[step] = SmtpFault.SILENCE

    with pytest.raises(EmailNoAnswerError):
        await SmtpEmailSender(settings).send(EMAIL)


async def test_a_silent_server_before_the_greeting_is_a_temporary_failure(
    scripted_smtp_settings: Settings, smtp_script: SmtpScript
) -> None:
    settings = scripted_smtp_settings.model_copy(update={"smtp_timeout": SHORT_TIMEOUT})
    smtp_script.replies["GREETING"] = SmtpFault.SILENCE

    with pytest.raises(EmailTemporaryError):
        await SmtpEmailSender(settings).send(EMAIL)


@pytest.mark.parametrize(
    ("replies", "error"),
    [
        pytest.param({"EHLO": "250 test"}, EmailRefusedError, id="no-starttls"),
        pytest.param({"STARTTLS": "454 Later"}, EmailTemporaryError, id="4xx"),
        pytest.param({"STARTTLS": "554 No"}, EmailRefusedError, id="5xx"),
        pytest.param({"STARTTLS": SmtpFault.CLOSE}, EmailNoAnswerError, id="closed"),
        pytest.param(
            {"STARTTLS": SmtpFault.BAD_TLS}, EmailTemporaryError, id="bad-handshake"
        ),
    ],
)
async def test_each_result_of_starttls_raises_its_error(
    scripted_smtp_settings: Settings,
    smtp_script: SmtpScript,
    replies: dict[str, str | SmtpFault],
    error: type[Exception],
) -> None:
    settings = scripted_smtp_settings.model_copy(
        update={"smtp_security": SmtpSecurity.STARTTLS}
    )
    smtp_script.replies.update(replies)

    with pytest.raises(error):
        await SmtpEmailSender(settings).send(EMAIL)


@pytest.mark.parametrize(
    ("replies", "error"),
    [
        pytest.param({"AUTH": "454 Later"}, EmailTemporaryError, id="4xx"),
        pytest.param({"AUTH": "535 Wrong"}, EmailRefusedError, id="5xx"),
        pytest.param({"AUTH": SmtpFault.CLOSE}, EmailNoAnswerError, id="closed"),
        pytest.param({"EHLO": "250 test"}, EmailRefusedError, id="no-auth"),
        pytest.param(
            {"EHLO": "250-test\r\n250 AUTH XOAUTH2"},
            EmailRefusedError,
            id="no-shared-method",
        ),
    ],
)
async def test_each_result_of_the_login_raises_its_error(
    scripted_smtp_settings: Settings,
    smtp_script: SmtpScript,
    replies: dict[str, str | SmtpFault],
    error: type[Exception],
) -> None:
    settings = scripted_smtp_settings.model_copy(
        update={"smtp_user": "ana", "smtp_password": SecretStr("hunter2")}
    )
    smtp_script.replies.update(replies)

    with pytest.raises(error):
        await SmtpEmailSender(settings).send(EMAIL)


@pytest.mark.parametrize(
    "reply",
    [
        pytest.param("not an SMTP reply", id="malformed"),
        pytest.param("200 Odd", id="2xx"),
    ],
)
async def test_a_reply_that_says_nothing_about_the_body_is_no_answer(
    scripted_smtp_settings: Settings, smtp_script: SmtpScript, reply: str
) -> None:
    smtp_script.replies["BODY"] = reply

    with pytest.raises(EmailNoAnswerError):
        await SmtpEmailSender(scripted_smtp_settings).send(EMAIL)


async def test_a_greeting_outside_4xx_and_5xx_is_a_temporary_failure(
    scripted_smtp_settings: Settings, smtp_script: SmtpScript
) -> None:
    smtp_script.replies["GREETING"] = "200 Odd"

    with pytest.raises(EmailTemporaryError):
        await SmtpEmailSender(scripted_smtp_settings).send(EMAIL)


@pytest.mark.parametrize(
    "reply",
    [
        pytest.param("500 No", id="5xx"),
        pytest.param(SmtpFault.CLOSE, id="closed"),
        pytest.param(SmtpFault.SILENCE, id="silent"),
    ],
)
async def test_a_failure_of_quit_after_the_accepted_body_raises_nothing(
    scripted_smtp_settings: Settings, smtp_script: SmtpScript, reply: str | SmtpFault
) -> None:
    settings = scripted_smtp_settings.model_copy(update={"smtp_timeout": SHORT_TIMEOUT})
    smtp_script.replies["QUIT"] = reply

    await SmtpEmailSender(settings).send(EMAIL)
