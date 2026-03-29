import pytest

from rastro.conta.domain.entities import User


def test_user_creation():
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    assert user.id == 1
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"


def test_user_is_frozen():
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    with pytest.raises(Exception):
        user.username = "newusername"
