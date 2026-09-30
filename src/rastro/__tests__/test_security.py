from http import HTTPStatus

from fastapi.testclient import TestClient

from rastro.config import get_settings
from rastro.main import create_app
from rastro.security import SECURITY_HEADERS, is_valid_csrf_token, issue_csrf_token

SECRET = b"secret"


def test_csrf_token_validates_for_its_session() -> None:
    token = issue_csrf_token(secret=SECRET, session_token="session")

    assert is_valid_csrf_token(token, secret=SECRET, session_token="session")


def test_csrf_token_does_not_validate_for_another_session() -> None:
    token = issue_csrf_token(secret=SECRET, session_token="session")

    assert not is_valid_csrf_token(token, secret=SECRET, session_token="other")
    assert not is_valid_csrf_token(token, secret=SECRET, session_token=None)


def test_csrf_token_does_not_validate_with_another_secret() -> None:
    token = issue_csrf_token(secret=SECRET, session_token=None)

    assert not is_valid_csrf_token(token, secret=b"other", session_token=None)


def test_csrf_token_without_a_signature_is_invalid() -> None:
    assert not is_valid_csrf_token("nonce", secret=SECRET, session_token=None)


def test_csrf_tokens_are_unique() -> None:
    first = issue_csrf_token(secret=SECRET, session_token=None)
    second = issue_csrf_token(secret=SECRET, session_token=None)

    assert first != second


def test_responses_carry_the_security_headers(client: TestClient) -> None:
    response = client.get("/api/v1/iam/session")

    for name, value in SECURITY_HEADERS:
        assert response.headers[name] == value


def test_unknown_host_is_rejected() -> None:
    client = TestClient(create_app(get_settings()), base_url="https://evil.example")

    response = client.get("/api/v1/iam/csrftoken")

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_api_docs_are_off_outside_debug(client: TestClient) -> None:
    assert client.get("/api/docs").status_code == HTTPStatus.NOT_FOUND
    assert client.get("/api/openapi.json").status_code == HTTPStatus.NOT_FOUND
