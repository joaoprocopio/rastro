import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.test import Client

from rastro.iam.models import Identity

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

SESSION_URL = "/api/v1/iam/session"
SESSION_START_URL = "/api/v1/iam/session/start"
CSRFTOKEN_URL = "/api/v1/iam/csrftoken"


def _post_json(
    client: Client, url: str, payload: dict[str, str]
) -> "_MonkeyPatchedWSGIResponse":
    return client.post(url, data=json.dumps(payload), content_type="application/json")


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
