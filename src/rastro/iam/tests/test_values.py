import pydantic
import pytest

from rastro.iam.values import DisplayName, Email, HashedPassword, RawPassword


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


def test_display_name_strips_spaces() -> None:
    assert DisplayName("  Ana  ").root == "Ana"


def test_display_name_allows_320_characters() -> None:
    assert len(DisplayName("a" * 320).root) == 320


def test_display_name_rejects_321_characters() -> None:
    with pytest.raises(pydantic.ValidationError):
        DisplayName("a" * 321)


def test_raw_password_keeps_its_spaces() -> None:
    assert RawPassword("  pass word  ").root == "  pass word  "


def test_raw_password_allows_8_characters() -> None:
    assert RawPassword("12345678").root == "12345678"


def test_raw_password_rejects_7_characters() -> None:
    with pytest.raises(pydantic.ValidationError):
        RawPassword("1234567")


def test_hashed_password_wraps_any_hash() -> None:
    assert HashedPassword("md5$salt$hash").root == "md5$salt$hash"
