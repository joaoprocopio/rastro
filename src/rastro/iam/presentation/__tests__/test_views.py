import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.test import Client

from rastro.iam.models import IdentityModel

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

IDENTITIES_URL = "/api/v1/iam/identities"
SESSION_URL = "/api/v1/iam/session"
CSRFTOKEN_URL = "/api/v1/iam/csrftoken"


def _post_json(
    client: Client, url: str, payload: dict[str, str]
) -> "_MonkeyPatchedWSGIResponse":
    return client.post(url, data=json.dumps(payload), content_type="application/json")


def test_register_returns_public_identity(client: Client, db: None) -> None:
    response = _post_json(
        client,
        IDENTITIES_URL,
        {
            "display_name": "Ada",
            "email": "ada@example.com",
            "password": "supersecret",
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {"display_name": "Ada", "email": "ada@example.com"}


def test_register_signs_the_identity_in(client: Client, db: None) -> None:
    _post_json(
        client,
        IDENTITIES_URL,
        {
            "display_name": "Ada",
            "email": "ada@example.com",
            "password": "supersecret",
        },
    )

    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"display_name": "Ada", "email": "ada@example.com"}


def test_authenticate_success(client: Client, identity: IdentityModel) -> None:
    response = _post_json(
        client,
        SESSION_URL,
        {"email": identity.email, "password": "password"},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "display_name": identity.display_name,
        "email": identity.email,
    }


def test_authenticate_wrong_password_and_unknown_email_are_identical(
    client: Client, identity: IdentityModel
) -> None:
    wrong_password = _post_json(
        client,
        SESSION_URL,
        {"email": identity.email, "password": "wrongpassword"},
    )
    unknown_email = _post_json(
        client,
        SESSION_URL,
        {"email": "nobody@example.com", "password": "wrongpassword"},
    )

    assert wrong_password.status_code == HTTPStatus.UNAUTHORIZED
    assert unknown_email.status_code == HTTPStatus.UNAUTHORIZED
    assert wrong_password["Content-Type"] == "application/problem+json"
    assert unknown_email["Content-Type"] == "application/problem+json"
    assert wrong_password.json() == unknown_email.json()


def test_current_identity_when_authenticated(
    client: Client, identity: IdentityModel
) -> None:
    _post_json(client, SESSION_URL, {"email": identity.email, "password": "password"})

    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "display_name": identity.display_name,
        "email": identity.email,
    }


def test_current_identity_when_unauthenticated(client: Client, db: None) -> None:
    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_end_session(client: Client, identity: IdentityModel) -> None:
    _post_json(client, SESSION_URL, {"email": identity.email, "password": "password"})

    end_response = client.delete(SESSION_URL)

    assert end_response.status_code == HTTPStatus.NO_CONTENT
    assert client.get(SESSION_URL).status_code == HTTPStatus.UNAUTHORIZED


def test_csrftoken_issues_cookie(client: Client, db: None) -> None:
    response = client.get(CSRFTOKEN_URL)

    assert response.status_code == HTTPStatus.OK
    assert "csrftoken" in response.cookies


def test_malformed_json_is_unprocessable(client: Client, db: None) -> None:
    response = client.post(
        IDENTITIES_URL, data="{not valid", content_type="application/json"
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response["Content-Type"] == "application/problem+json"
