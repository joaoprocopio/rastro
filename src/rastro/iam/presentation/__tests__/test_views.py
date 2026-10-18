import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.test import Client

from rastro.iam.models import Identity

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

IDENTITIES_URL = "/api/v1/iam/identities"
SESSION_URL = "/api/v1/iam/session"
SESSION_START_URL = "/api/v1/iam/session/start"
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


def test_current_identity_when_authenticated(
    client: Client, identity: Identity
) -> None:
    _post_json(
        client,
        SESSION_START_URL,
        {"email": identity.email.value, "password": "password"},
    )

    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "display_name": identity.display_name.value,
        "email": identity.email.value,
    }


def test_current_identity_when_unauthenticated(client: Client, db: None) -> None:
    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/iam.not_authenticated",
        "status": 401,
    }


def test_end_session(client: Client, identity: Identity) -> None:
    _post_json(
        client,
        SESSION_START_URL,
        {"email": identity.email.value, "password": "password"},
    )

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
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#", "type": "/problems/request.invalid_json"}],
    }


def test_register_keeps_the_spaces_of_the_password(client: Client, db: None) -> None:
    _post_json(
        client,
        IDENTITIES_URL,
        {
            "display_name": "Ada",
            "email": "ada@example.com",
            "password": "  pass word  ",
        },
    )
    client.delete(SESSION_URL)

    response = _post_json(
        client, SESSION_START_URL, {"email": "ada@example.com", "password": "pass word"}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
