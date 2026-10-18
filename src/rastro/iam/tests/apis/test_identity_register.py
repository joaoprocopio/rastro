import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.test import Client

from rastro.iam.models import Identity

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

IDENTITY_REGISTER_URL = "/api/v1/iam/identities/register"
SESSION_URL = "/api/v1/iam/session"
SESSION_START_URL = "/api/v1/iam/session/start"

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


def _start_session(
    client: Client, payload: dict[str, str]
) -> "_MonkeyPatchedWSGIResponse":
    return client.post(
        SESSION_START_URL, data=json.dumps(payload), content_type="application/json"
    )


def test_a_valid_body_registers_the_identity_with_no_body(
    client: Client, db: None
) -> None:
    response = _register(client, VALID_PAYLOAD)

    assert response.status_code == HTTPStatus.CREATED
    assert response.content == b""


def test_registration_starts_no_session(client: Client, db: None) -> None:
    _register(client, VALID_PAYLOAD)

    response = client.get(SESSION_URL)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"type": "/problems/iam.not_authenticated", "status": 401}


def test_an_email_in_use_is_a_conflict(client: Client, identity: Identity) -> None:
    response = _register(client, {**VALID_PAYLOAD, "email": identity.email.value})

    assert response.status_code == HTTPStatus.CONFLICT
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "/problems/iam.email_in_use", "status": 409}


def test_an_invalid_field_points_at_the_field_with_the_value_object_code(
    client: Client, db: None
) -> None:
    response = _register(
        client,
        {"email": "nope", "display_name": "x" * 321, "password": "short"},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/email", "type": "/problems/iam.invalid_email"},
            {
                "pointer": "#/display_name",
                "type": "/problems/iam.invalid_display_name",
            },
            {"pointer": "#/password", "type": "/problems/iam.invalid_password"},
        ],
    }


def test_the_email_is_stripped_and_lowercased(client: Client, db: None) -> None:
    _register(client, {**VALID_PAYLOAD, "email": " Ana@X.com "})

    response = _start_session(client, {"email": "ana@x.com", "password": "supersecret"})

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_a_get_is_a_problem_405(client: Client, db: None) -> None:
    response = client.get(IDENTITY_REGISTER_URL)

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response["Content-Type"] == "application/problem+json"
    assert response["Allow"] == "POST"
    assert response.json() == {"status": 405}


def test_a_request_without_a_csrf_token_is_a_problem_403(db: None) -> None:
    client = Client(enforce_csrf_checks=True)

    response = _register(client, VALID_PAYLOAD)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "/problems/request.csrf_failed", "status": 403}


def test_the_password_keeps_its_spaces(client: Client, db: None) -> None:
    _register(client, {**VALID_PAYLOAD, "password": "  pass word  "})

    trimmed = _start_session(
        client, {"email": "ada@example.com", "password": "pass word"}
    )
    exact = _start_session(
        client, {"email": "ada@example.com", "password": "  pass word  "}
    )

    assert trimmed.status_code == HTTPStatus.UNAUTHORIZED
    assert exact.status_code == HTTPStatus.NO_CONTENT
