import pytest
from unittest.mock import Mock

from rastro.conta.domain.entities import User
from rastro.conta.domain.exceptions import AuthenticationError
from rastro.conta.application.dto import AuthenticateUserInput
from rastro.conta.application.use_cases.authenticate_user import AuthenticateUserUseCase


def test_authenticate_user_by_email_success():
    user_repo = Mock()
    user_repo.get_by_email.return_value = User(
        id=1,
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    user_repo.verify_password.return_value = True

    use_case = AuthenticateUserUseCase(user_repo)
    result = use_case.execute(
        AuthenticateUserInput(query="test@example.com", password="password")
    )

    assert result.id == 1
    assert result.username == "testuser"
    user_repo.get_by_email.assert_called_once_with("test@example.com")


def test_authenticate_user_by_username_success():
    user_repo = Mock()
    user_repo.get_by_username.return_value = User(
        id=1,
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    user_repo.verify_password.return_value = True

    use_case = AuthenticateUserUseCase(user_repo)
    result = use_case.execute(
        AuthenticateUserInput(query="testuser", password="password")
    )

    assert result.id == 1
    user_repo.get_by_username.assert_called_once_with("testuser")


def test_authenticate_user_invalid_credentials():
    user_repo = Mock()
    user_repo.get_by_email.return_value = None

    use_case = AuthenticateUserUseCase(user_repo)

    with pytest.raises(AuthenticationError):
        use_case.execute(
            AuthenticateUserInput(query="test@example.com", password="wrong")
        )
