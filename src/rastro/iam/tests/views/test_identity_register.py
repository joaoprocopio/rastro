from http import HTTPStatus

from django.test import Client
from django.urls import reverse

from rastro.iam.models import Identity

VALID_PAYLOAD = {
    "email": "ada@example.com",
    "display_name": "Ada",
    "password": "supersecret",
}


def test_a_valid_body_registers_the_identity_with_no_body(
    client: Client, db: None
) -> None:
    response = client.post(
        reverse("iam:identity_register"),
        VALID_PAYLOAD,
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.content == b""


def test_registration_starts_no_session(client: Client, db: None) -> None:
    client.post(
        reverse("iam:identity_register"),
        VALID_PAYLOAD,
        content_type="application/json",
    )

    response = client.get(reverse("iam:session_current"))

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"type": "/problems/iam.not_authenticated", "status": 401}


def test_an_email_in_use_is_a_conflict(client: Client, identity: Identity) -> None:
    response = client.post(
        reverse("iam:identity_register"),
        {**VALID_PAYLOAD, "email": identity.email.value},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "/problems/iam.email_in_use", "status": 409}


def test_an_invalid_field_points_at_the_field_with_the_value_object_code(
    client: Client, db: None
) -> None:
    response = client.post(
        reverse("iam:identity_register"),
        {"email": "nope", "display_name": "x" * 321, "password": "short"},
        content_type="application/json",
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


def test_an_email_longer_than_254_characters_is_a_validation_error(
    client: Client, db: None
) -> None:
    local_part = "a" * (296 - len("@example.com"))

    response = client.post(
        reverse("iam:identity_register"),
        {**VALID_PAYLOAD, "email": f"{local_part}@example.com"},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#/email", "type": "/problems/iam.invalid_email"}],
    }


def test_the_email_is_stripped_and_lowercased(client: Client, db: None) -> None:
    client.post(
        reverse("iam:identity_register"),
        {**VALID_PAYLOAD, "email": " Ana@X.com "},
        content_type="application/json",
    )

    response = client.post(
        reverse("iam:session_start"),
        {"email": "ana@x.com", "password": "supersecret"},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_a_get_is_a_problem_405(client: Client, db: None) -> None:
    response = client.get(reverse("iam:identity_register"))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response["Content-Type"] == "application/problem+json"
    assert response["Allow"] == "POST"
    assert response.json() == {"status": 405}


def test_a_request_without_a_csrf_token_is_a_problem_403(db: None) -> None:
    client = Client(enforce_csrf_checks=True)

    response = client.post(
        reverse("iam:identity_register"),
        VALID_PAYLOAD,
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "/problems/request.csrf_failed", "status": 403}


def test_the_password_keeps_its_spaces(client: Client, db: None) -> None:
    client.post(
        reverse("iam:identity_register"),
        {**VALID_PAYLOAD, "password": "  pass word  "},
        content_type="application/json",
    )

    trimmed = client.post(
        reverse("iam:session_start"),
        {"email": "ada@example.com", "password": "pass word"},
        content_type="application/json",
    )
    exact = client.post(
        reverse("iam:session_start"),
        {"email": "ada@example.com", "password": "  pass word  "},
        content_type="application/json",
    )

    assert trimmed.status_code == HTTPStatus.UNAUTHORIZED
    assert exact.status_code == HTTPStatus.NO_CONTENT
