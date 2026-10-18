import pytest

from rastro.common.values import InvalidValueError
from rastro.iam.values import DisplayName, Email, HashedPassword, RawPassword


def test_email_strips_spaces_and_lowercases_the_whole_address() -> None:
    assert Email(" Ana@X.com ").value == "ana@x.com"


def test_email_turns_a_full_width_address_into_its_plain_form() -> None:
    assert Email("ａｎａ＠ｘ.ｃｏｍ").value == "ana@x.com"


@pytest.mark.parametrize("raw", ["", "ana", "ana@", "@x.com", "ana@x", "a na@x.com"])
def test_email_rejects_an_invalid_address(raw: str) -> None:
    with pytest.raises(InvalidValueError) as excinfo:
        Email(raw)

    assert excinfo.value.code == "iam.invalid_email"


def test_display_name_strips_spaces() -> None:
    assert DisplayName("  Ana  ").value == "Ana"


def test_display_name_allows_320_characters() -> None:
    assert len(DisplayName("a" * 320).value) == 320


def test_display_name_rejects_321_characters() -> None:
    with pytest.raises(InvalidValueError) as excinfo:
        DisplayName("a" * 321)

    assert excinfo.value.code == "iam.invalid_display_name"


def test_raw_password_keeps_its_spaces() -> None:
    assert RawPassword("  pass word  ").value == "  pass word  "


def test_raw_password_allows_8_characters() -> None:
    assert RawPassword("12345678").value == "12345678"


def test_raw_password_rejects_7_characters() -> None:
    with pytest.raises(InvalidValueError) as excinfo:
        RawPassword("1234567")

    assert excinfo.value.code == "iam.invalid_password"


def test_hashed_password_wraps_any_hash() -> None:
    assert HashedPassword("md5$salt$hash").value == "md5$salt$hash"
