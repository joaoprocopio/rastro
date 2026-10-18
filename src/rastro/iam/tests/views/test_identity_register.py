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
        {**VALID_PAYLOAD, "email": identity.email.root},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "/problems/iam.email_in_use", "status": 409}


def test_each_invalid_field_names_the_rule_that_failed(
    client: Client, db: None
) -> None:
    response = client.post(
        reverse("iam:identity_register"),
        {"email": "nope", "display_name": "Ada", "password": "short"},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/email", "type": "/problems/request.invalid_format"},
            {
                "pointer": "#/password",
                "type": "/problems/request.too_short",
                "min_length": 8,
            },
        ],
    }
    assert not Identity.objects.exists()


def test_an_email_longer_than_254_characters_is_too_long(
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
        "errors": [
            {
                "pointer": "#/email",
                "type": "/problems/request.too_long",
                "max_length": 254,
            }
        ],
    }


def test_a_display_name_longer_than_320_characters_is_too_long(
    client: Client, db: None
) -> None:
    response = client.post(
        reverse("iam:identity_register"),
        {**VALID_PAYLOAD, "display_name": "x" * 321},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [
            {
                "pointer": "#/display_name",
                "type": "/problems/request.too_long",
                "max_length": 320,
            }
        ],
    }


def test_a_missing_field_a_wrong_type_and_an_unknown_field_keep_their_types(
    client: Client, db: None
) -> None:
    response = client.post(
        reverse("iam:identity_register"),
        {"email": 1, "password": "supersecret", "role": "admin"},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/role", "type": "/problems/request.unknown_field"},
            {"pointer": "#/email", "type": "/problems/request.invalid_type"},
            {"pointer": "#/display_name", "type": "/problems/request.field_required"},
        ],
    }


def test_malformed_json_keeps_its_type(client: Client, db: None) -> None:
    response = client.post(
        reverse("iam:identity_register"), "{not valid", content_type="application/json"
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#", "type": "/problems/request.invalid_json"}],
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
    assert response.json() == {
        "type": "/problems/request.method_not_allowed",
        "status": 405,
    }


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
