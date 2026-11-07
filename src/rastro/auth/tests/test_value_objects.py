from datetime import timedelta

import pydantic
import pytest
from pydantic import SecretStr

from rastro.auth.domain.value_objects import (
    DisplayName,
    Email,
    HashedPassword,
    HashedResetToken,
    HashedSessionToken,
    OutgoingEmail,
    RawPassword,
    ResetLinkUrl,
    ResetToken,
    ResetTokenCooldown,
    ResetTokenLifetime,
    SessionLifetime,
    SessionToken,
)
from rastro.common.domain.value_objects import TokenBytes

ONE_HOUR = ResetTokenLifetime(timedelta(hours=1))


def test_email_strips_spaces_and_lowercases_the_whole_address() -> None:
    assert Email(" Ana@X.com ").root == "ana@x.com"


def test_email_turns_a_full_width_address_into_its_plain_form() -> None:
    assert Email("ａｎａ＠ｘ.ｃｏｍ").root == "ana@x.com"


@pytest.mark.parametrize("raw", ["", "ana", "ana@", "@x.com", "ana@x", "a na@x.com"])
def test_email_rejects_an_invalid_address(raw: str) -> None:
    with pytest.raises(pydantic.ValidationError):
        Email(raw)


def test_email_allows_254_characters() -> None:
    local_part = "a" * (254 - len("@example.com"))

    assert len(Email(f"{local_part}@example.com").root) == 254


def test_email_rejects_255_characters() -> None:
    local_part = "a" * (255 - len("@example.com"))

    with pytest.raises(pydantic.ValidationError):
        Email(f"{local_part}@example.com")


def test_email_rejects_a_value_that_is_not_a_string() -> None:
    with pytest.raises(pydantic.ValidationError):
        Email.model_validate(1)


def test_email_accepts_an_email_as_its_input() -> None:
    email = Email("ana@x.com")

    assert Email.model_validate(email) == email


def test_email_is_frozen() -> None:
    email = Email("ana@x.com")

    with pytest.raises(pydantic.ValidationError):
        email.root = "bia@x.com"  # type: ignore[misc]


def test_a_rejected_email_keeps_the_input_out_of_the_message() -> None:
    with pytest.raises(pydantic.ValidationError) as excinfo:
        Email("secret-address")

    assert "secret-address" not in str(excinfo.value)


def test_display_name_strips_spaces() -> None:
    assert DisplayName("  Ana  ").root == "Ana"


def test_display_name_allows_320_characters() -> None:
    assert len(DisplayName("a" * 320).root) == 320


def test_display_name_rejects_321_characters() -> None:
    with pytest.raises(pydantic.ValidationError):
        DisplayName("a" * 321)


def test_raw_password_keeps_its_spaces() -> None:
    assert (
        RawPassword.model_validate("  pass word  ").root.get_secret_value()
        == "  pass word  "
    )


def test_raw_password_allows_8_characters() -> None:
    assert RawPassword.model_validate("12345678").root.get_secret_value() == "12345678"


def test_raw_password_rejects_7_characters() -> None:
    with pytest.raises(pydantic.ValidationError):
        RawPassword.model_validate("1234567")


@pytest.mark.parametrize("raw", ["\ud800aaaaaaaa", SecretStr("\ud800aaaaaaaa")])
def test_raw_password_rejects_a_lone_surrogate(raw: str | SecretStr) -> None:
    with pytest.raises(pydantic.ValidationError) as excinfo:
        RawPassword.model_validate(raw)

    assert [error["type"] for error in excinfo.value.errors()] == ["string_unicode"]


def test_a_rejected_password_keeps_the_input_out_of_the_message() -> None:
    with pytest.raises(pydantic.ValidationError) as excinfo:
        RawPassword.model_validate("hunter2")

    assert "hunter2" not in str(excinfo.value)


def test_hashed_password_wraps_any_hash() -> None:
    assert HashedPassword("md5$salt$hash").root == "md5$salt$hash"


def test_the_digest_of_a_session_token_is_its_sha256() -> None:
    # The SHA-256 of "abc" from FIPS 180-2, appendix B.1.
    expected = bytes.fromhex(
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )

    assert SessionToken(SecretStr("abc")).digest() == HashedSessionToken(expected)


def test_a_new_session_token_of_16_bytes_has_22_characters() -> None:
    token = SessionToken.generate(nbytes=TokenBytes(16))

    assert len(token.root.get_secret_value()) == 22


def test_two_new_session_tokens_differ() -> None:
    assert SessionToken.generate(nbytes=TokenBytes(16)) != SessionToken.generate(
        nbytes=TokenBytes(16)
    )


def test_the_digest_of_a_reset_token_is_its_sha256() -> None:
    # The SHA-256 of "abc" from FIPS 180-2, appendix B.1.
    expected = bytes.fromhex(
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )

    assert ResetToken(SecretStr("abc")).digest() == HashedResetToken(expected)


def test_a_new_reset_token_of_16_bytes_has_22_characters() -> None:
    token = ResetToken.generate(nbytes=TokenBytes(16))

    assert len(token.root.get_secret_value()) == 22


def test_two_new_reset_tokens_differ() -> None:
    assert ResetToken.generate(nbytes=TokenBytes(16)) != ResetToken.generate(
        nbytes=TokenBytes(16)
    )


def test_a_reset_token_has_no_format_rule() -> None:
    assert ResetToken.model_validate("").root.get_secret_value() == ""


def test_a_reset_token_with_a_lone_surrogate_has_a_digest() -> None:
    token = ResetToken.model_validate("\ud800")

    assert token.digest() == ResetToken.model_validate("\ud800").digest()


@pytest.mark.parametrize(
    "secret",
    [
        RawPassword(SecretStr("hunter22")),
        SessionToken(SecretStr("abc")),
        ResetToken(SecretStr("abc")),
    ],
    ids=type,
)
def test_the_repr_of_a_secret_hides_its_value(
    secret: RawPassword | SessionToken | ResetToken,
) -> None:
    assert "**********" in repr(secret)
    assert secret.root.get_secret_value() not in repr(secret)


@pytest.mark.parametrize("lifetime", [timedelta(0), timedelta(hours=-1)])
def test_session_lifetime_rejects_a_duration_of_zero_or_less(
    lifetime: timedelta,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        SessionLifetime(lifetime)


@pytest.mark.parametrize("lifetime", [timedelta(0), timedelta(hours=-1)])
def test_reset_token_lifetime_rejects_a_duration_of_zero_or_less(
    lifetime: timedelta,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        ResetTokenLifetime(lifetime)


@pytest.mark.parametrize("cooldown", [timedelta(0), timedelta(seconds=-1)])
def test_reset_token_cooldown_rejects_a_duration_of_zero_or_less(
    cooldown: timedelta,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        ResetTokenCooldown(cooldown)


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:5173/password-reset",
        "https://rastro.example/password-reset?source=email",
    ],
)
def test_reset_link_url_accepts_a_web_address(url: str) -> None:
    assert ResetLinkUrl(url).root == url


@pytest.mark.parametrize(
    "url",
    ["", "rastro.example/reset", "ftp://rastro.example", "https://x.com/#/reset"],
)
def test_reset_link_url_rejects_another_scheme_or_a_fragment(url: str) -> None:
    with pytest.raises(pydantic.ValidationError):
        ResetLinkUrl(url)


@pytest.mark.parametrize(
    ("lifetime", "words"),
    [
        (timedelta(hours=1), "1 hour"),
        (timedelta(hours=2), "2 hours"),
        (timedelta(minutes=1), "1 minute"),
        (timedelta(minutes=90), "90 minutes"),
        (timedelta(seconds=1), "1 second"),
        (timedelta(seconds=45), "45 seconds"),
    ],
)
def test_a_password_reset_email_states_the_lifetime_in_words(
    lifetime: timedelta, words: str
) -> None:
    email = _password_reset_email(lifetime=ResetTokenLifetime(lifetime))

    assert f"The link works for {words} and only once" in (
        email.body.get_secret_value()
    )


def test_a_password_reset_email_holds_the_token_in_the_fragment_of_its_link() -> None:
    email = _password_reset_email()

    assert email.to == Email("ana@x.com")
    assert email.subject == "Reset your rastro password"
    assert email.body.get_secret_value().splitlines() == [
        "Someone asked to reset your rastro password.",
        "",
        (
            "To choose a new password, open this link. "
            "The link works for 1 hour and only once:"
        ),
        "",
        "https://rastro.example/password-reset#token=abc",
        "",
        "If you did not ask for this, ignore this email. Your password stays the same.",
    ]


def test_the_repr_of_a_password_reset_email_hides_the_token() -> None:
    assert "abc" not in repr(_password_reset_email())


def _password_reset_email(*, lifetime: ResetTokenLifetime = ONE_HOUR) -> OutgoingEmail:
    return OutgoingEmail.password_reset(
        to=Email("ana@x.com"),
        link_url=ResetLinkUrl("https://rastro.example/password-reset"),
        token=ResetToken(SecretStr("abc")),
        lifetime=lifetime,
    )
