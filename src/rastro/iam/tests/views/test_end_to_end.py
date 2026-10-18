import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.conf import settings
from django.test import Client

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

CSRF_URL = "/api/v1/iam/csrf"
IDENTITY_REGISTER_URL = "/api/v1/iam/identities/register"
SESSION_URL = "/api/v1/iam/session"
SESSION_START_URL = "/api/v1/iam/session/start"
SESSION_END_URL = "/api/v1/iam/session/end"

NOT_AUTHENTICATED = {"type": "/problems/iam.not_authenticated", "status": 401}


def _post(
    client: Client, url: str, payload: dict[str, str] | None = None
) -> "_MonkeyPatchedWSGIResponse":
    return client.post(
        url,
        data=json.dumps(payload) if payload is not None else None,
        content_type="application/json",
        headers={"X-CSRFToken": client.cookies["csrftoken"].value},
    )


def test_a_person_registers_starts_reads_and_ends_a_session(db: None) -> None:
    client = Client(enforce_csrf_checks=True)

    csrf = client.get(CSRF_URL)
    assert csrf.status_code == HTTPStatus.NO_CONTENT
    assert csrf.content == b""
    assert csrf.cookies["csrftoken"].value

    register = _post(
        client,
        IDENTITY_REGISTER_URL,
        {"email": "Ada@Example.com", "display_name": "Ada", "password": "supersecret"},
    )
    assert register.status_code == HTTPStatus.CREATED
    assert register.content == b""

    before_start = client.get(SESSION_URL)
    assert before_start.status_code == HTTPStatus.UNAUTHORIZED
    assert before_start["Content-Type"] == "application/problem+json"
    assert before_start.json() == NOT_AUTHENTICATED

    start = _post(
        client,
        SESSION_START_URL,
        {"email": "ada@example.com", "password": "supersecret"},
    )
    assert start.status_code == HTTPStatus.NO_CONTENT
    assert start.content == b""
    assert settings.SESSION_COOKIE_NAME in start.cookies

    current = client.get(SESSION_URL)
    assert current.status_code == HTTPStatus.OK
    assert current["Content-Type"] == "application/json"
    assert current.json() == {"email": "ada@example.com", "display_name": "Ada"}

    end = _post(client, SESSION_END_URL)
    assert end.status_code == HTTPStatus.NO_CONTENT
    assert end.content == b""

    after_end = client.get(SESSION_URL)
    assert after_end.status_code == HTTPStatus.UNAUTHORIZED
    assert after_end.json() == NOT_AUTHENTICATED
