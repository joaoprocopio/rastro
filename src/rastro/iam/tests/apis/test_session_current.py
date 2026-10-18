import json
from http import HTTPStatus

from django.test import Client

from rastro.iam.models import Identity

SESSION_URL = "/api/v1/iam/session"
SESSION_START_URL = "/api/v1/iam/session/start"


def _start_session(client: Client, identity: Identity) -> None:
    client.post(
        SESSION_START_URL,
        data=json.dumps({"email": identity.email.value, "password": "password"}),
        content_type="application/json",
    )


def test_a_session_answers_the_email_and_display_name_of_its_identity(
    client: Client, identity: Identity
) -> None:
    _start_session(client, identity)

    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.OK
    assert response["Content-Type"] == "application/json"
    assert response.json() == {
        "email": identity.email.value,
        "display_name": identity.display_name.value,
    }


def test_no_session_answers_the_not_authenticated_problem(
    client: Client, db: None
) -> None:
    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/iam.not_authenticated",
        "status": 401,
    }
