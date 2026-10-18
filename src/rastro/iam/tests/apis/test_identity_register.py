import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.test import Client

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

IDENTITY_REGISTER_URL = "/api/v1/iam/identities/register"

VALID_PAYLOAD = {
    "email": "ada@example.com",
    "display_name": "Ada",
    "password": "supersecret",
}


def _register(
    client: Client, payload: dict[str, object]
) -> "_MonkeyPatchedWSGIResponse":
    return client.post(
        IDENTITY_REGISTER_URL,
        data=json.dumps(payload),
        content_type="application/json",
    )


def test_a_valid_body_registers_the_identity_with_no_body(
    client: Client, db: None
) -> None:
    response = _register(client, VALID_PAYLOAD)

    assert response.status_code == HTTPStatus.CREATED
    assert response.content == b""
