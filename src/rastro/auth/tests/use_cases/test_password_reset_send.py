from datetime import timedelta

import pytest

from rastro.auth.application.dtos import PasswordResetSendInput, PasswordResetSendOutput
from rastro.auth.application.use_cases import password_reset_send
from rastro.auth.domain.aggregates import IssuedResetToken, User
from rastro.auth.domain.errors import (
    EmailNoAnswerError,
    EmailRefusedError,
    EmailTemporaryError,
)
from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    ResetLinkUrl,
    ResetToken,
    ResetTokenCooldown,
)
from rastro.auth.tests.fakes import (
    FakeClock,
    FakeEmailSender,
    FakeResetTokenRepository,
    FakeUserRepository,
)
from rastro.auth.tests.use_cases.conftest import RESET_TOKEN_LIFETIME
from rastro.common.domain.value_objects import TokenBytes

ANA = PasswordResetSendInput(email=Email("ana@x.com"))
LINK_URL = ResetLinkUrl("https://rastro.example/password-reset")
TOKEN_BYTES = TokenBytes(16)
COOLDOWN = ResetTokenCooldown(timedelta(seconds=60))


async def _send(
    input: PasswordResetSendInput,
    *,
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    cooldown: ResetTokenCooldown = COOLDOWN,
) -> PasswordResetSendOutput:
    return await password_reset_send(
        input,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
        lifetime=RESET_TOKEN_LIFETIME,
        cooldown=cooldown,
        token_bytes=TOKEN_BYTES,
        link_url=LINK_URL,
    )


async def test_an_address_with_no_user_sends_nothing_and_stores_nothing(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
) -> None:
    await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    assert email_sender.sent == []
    assert reset_tokens.reset_tokens == {}


async def test_a_user_receives_one_email_at_the_address_of_the_user(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    ana: User,
) -> None:
    await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    (email,) = email_sender.sent
    assert email.to == ana.email


async def test_the_link_of_the_email_holds_a_token_of_the_configured_size(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    ana: User,
) -> None:
    await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    token = email_sender.last_reset_token()
    assert f"{LINK_URL.root}#token={token.root.get_secret_value()}" in (
        email_sender.sent[-1].body.get_secret_value()
    )
    # 16 random bytes take 22 characters of base64.
    assert len(token.root.get_secret_value()) == 22


async def test_the_stored_row_holds_the_digest_of_the_token_of_the_email(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    ana: User,
) -> None:
    await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    stored = await reset_tokens.get_by_user_id(ana.id)
    assert stored is not None
    assert stored == IssuedResetToken(
        id=stored.id,
        user_id=ana.id,
        hashed_token=email_sender.last_reset_token().digest(),
        issued_at=clock.now(),
        expires_at=clock.now() + timedelta(hours=1),
    )


async def test_a_send_after_the_cooldown_replaces_the_token_of_the_user(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    ana: User,
    reset_token: ResetToken,
) -> None:
    clock.current += timedelta(seconds=61)

    await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    stored = await reset_tokens.get_by_user_id(ana.id)
    assert stored is not None
    assert stored.hashed_token != reset_token.digest()
    assert stored.hashed_token == email_sender.last_reset_token().digest()
    assert stored.issued_at == clock.now()


async def test_a_send_within_the_cooldown_sends_nothing_and_keeps_the_token(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    ana: User,
    reset_token: ResetToken,
) -> None:
    before = await reset_tokens.get_by_user_id(ana.id)
    clock.current += timedelta(seconds=59)

    await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    assert email_sender.sent == []
    assert await reset_tokens.get_by_user_id(ana.id) == before


async def test_a_send_at_the_moment_the_cooldown_ends_sends_the_email(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    reset_token: ResetToken,
) -> None:
    clock.current += timedelta(seconds=60)

    await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    assert len(email_sender.sent) == 1


@pytest.mark.parametrize(
    ("cooldown", "emails"),
    [
        (ResetTokenCooldown(timedelta(seconds=1)), 1),
        (ResetTokenCooldown(timedelta(minutes=10)), 0),
    ],
)
async def test_the_send_applies_the_cooldown_it_receives(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    reset_token: ResetToken,
    cooldown: ResetTokenCooldown,
    emails: int,
) -> None:
    clock.current += timedelta(seconds=61)

    await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
        cooldown=cooldown,
    )

    assert len(email_sender.sent) == emails


async def test_a_young_token_of_another_user_does_not_hold_the_email(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    reset_token: ResetToken,
) -> None:
    bia = User(
        id=await users.next_id(),
        email=Email("bia@x.com"),
        display_name=DisplayName("Bia"),
        hashed_password=HashedPassword("fake$password"),
    )
    await users.add(bia)

    await _send(
        PasswordResetSendInput(email=bia.email),
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    (email,) = email_sender.sent
    assert email.to == bia.email


async def test_an_accepted_send_reports_an_answer(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    ana: User,
) -> None:
    output = await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    assert output == PasswordResetSendOutput(no_answer=False)


async def test_an_address_with_no_user_reports_an_answer(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
) -> None:
    output = await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    assert output == PasswordResetSendOutput(no_answer=False)


async def test_a_send_within_the_cooldown_reports_an_answer(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    reset_token: ResetToken,
) -> None:
    output = await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    assert output == PasswordResetSendOutput(no_answer=False)


async def test_a_send_with_no_answer_keeps_the_token_and_reports_it(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    ana: User,
) -> None:
    email_sender.error = EmailNoAnswerError()

    output = await _send(
        ANA,
        users=users,
        reset_tokens=reset_tokens,
        email_sender=email_sender,
        clock=clock,
    )

    assert output == PasswordResetSendOutput(no_answer=True)
    assert await reset_tokens.get_by_user_id(ana.id) is not None


@pytest.mark.parametrize("error", [EmailTemporaryError, EmailRefusedError])
async def test_a_send_that_did_not_go_out_raises_its_error(
    users: FakeUserRepository,
    reset_tokens: FakeResetTokenRepository,
    email_sender: FakeEmailSender,
    clock: FakeClock,
    ana: User,
    error: type[Exception],
) -> None:
    email_sender.error = error()

    with pytest.raises(error):
        await _send(
            ANA,
            users=users,
            reset_tokens=reset_tokens,
            email_sender=email_sender,
            clock=clock,
        )
