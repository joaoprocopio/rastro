import json
from http import HTTPStatus

from django.test import Client

from rastro.iam.models import Identity

SESSION_URL = "/api/v1/iam/session"
SESSION_START_URL = "/api/v1/iam/session/start"
SESSION_END_URL = "/api/v1/iam/session/end"


def _start_session(client: Client, identity: Identity) -> None:
    client.post(
        SESSION_START_URL,
        data=json.dumps({"email": identity.email.value, "password": "password"}),
        content_type="application/json",
    )


def test_ends_the_session(client: Client, identity: Identity) -> None:
    _start_session(client, identity)
    assert client.get(SESSION_URL).status_code == HTTPStatus.OK

    response = client.post(SESSION_END_URL)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert client.get(SESSION_URL).status_code == HTTPStatus.UNAUTHORIZED


def test_succeeds_without_a_session(client: Client, db: None) -> None:
    response = client.post(SESSION_END_URL)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
