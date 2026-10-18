import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.test import Client


if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

IDENTITIES_URL = "/api/v1/iam/identities"
SESSION_URL = "/api/v1/iam/session"
SESSION_START_URL = "/api/v1/iam/session/start"
SESSION_END_URL = "/api/v1/iam/session/end"


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
    client.post(SESSION_END_URL)

    response = _post_json(
        client, SESSION_START_URL, {"email": "ada@example.com", "password": "pass word"}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
