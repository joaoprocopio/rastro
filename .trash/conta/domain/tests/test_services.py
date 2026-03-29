import pytest

from rastro.conta.domain.services import is_email


@pytest.mark.parametrize(
    "value,expected",
    [
        ("test@example.com", True),
        ("user@domain.org", True),
        ("invalid", False),
        ("n@s", True),
        ("", False),
        ("user@", True),
        ("@domain.com", True),
    ],
)
def test_is_email(value: str, expected: bool):
    assert is_email(value) == expected
