from http import HTTPStatus

from django.conf import settings
from django.test import Client
from django.urls import reverse

NOT_AUTHENTICATED = {"type": "/problems/iam.not_authenticated", "status": 401}


def test_a_person_registers_starts_reads_and_ends_a_session(db: None) -> None:
    client = Client(enforce_csrf_checks=True)

    csrf = client.get(reverse("iam:csrf_get"))
    assert csrf.status_code == HTTPStatus.NO_CONTENT
    assert csrf.content == b""
    assert csrf.cookies["csrftoken"].value

    register = client.post(
        reverse("iam:identity_register"),
        {"email": "Ada@Example.com", "display_name": "Ada", "password": "supersecret"},
        content_type="application/json",
        headers={"X-CSRFToken": client.cookies["csrftoken"].value},
    )
    assert register.status_code == HTTPStatus.CREATED
    assert register.content == b""

    before_start = client.get(reverse("iam:session_current"))
    assert before_start.status_code == HTTPStatus.UNAUTHORIZED
    assert before_start["Content-Type"] == "application/problem+json"
    assert before_start.json() == NOT_AUTHENTICATED

    start = client.post(
        reverse("iam:session_start"),
        {"email": "ada@example.com", "password": "supersecret"},
        content_type="application/json",
        headers={"X-CSRFToken": client.cookies["csrftoken"].value},
    )
    assert start.status_code == HTTPStatus.NO_CONTENT
    assert start.content == b""
    assert settings.SESSION_COOKIE_NAME in start.cookies

    current = client.get(reverse("iam:session_current"))
    assert current.status_code == HTTPStatus.OK
    assert current["Content-Type"] == "application/json"
    assert current.json() == {"email": "ada@example.com", "display_name": "Ada"}

    end = client.post(
        reverse("iam:session_end"),
        content_type="application/json",
        headers={"X-CSRFToken": client.cookies["csrftoken"].value},
    )
    assert end.status_code == HTTPStatus.NO_CONTENT
    assert end.content == b""

    after_end = client.get(reverse("iam:session_current"))
    assert after_end.status_code == HTTPStatus.UNAUTHORIZED
    assert after_end.json() == NOT_AUTHENTICATED
