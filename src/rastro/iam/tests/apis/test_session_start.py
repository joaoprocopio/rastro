import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.conf import settings
from django.test import Client

from rastro.iam.models import Identity

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

SESSION_START_URL = "/api/v1/iam/session/start"


def _start_session(
    client: Client, payload: dict[str, str]
) -> "_MonkeyPatchedWSGIResponse":
    return client.post(
        SESSION_START_URL, data=json.dumps(payload), content_type="application/json"
    )


def test_correct_credentials_start_a_session(
    client: Client, identity: Identity
) -> None:
    response = _start_session(
        client, {"email": identity.email.value, "password": "password"}
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert settings.SESSION_COOKIE_NAME in response.cookies
