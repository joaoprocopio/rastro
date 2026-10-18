from http import HTTPStatus

from django.test import Client
from django.urls import reverse

from rastro.iam.models import Identity


def test_a_session_answers_the_email_and_display_name_of_its_identity(
    signed_in_client: Client, identity: Identity
) -> None:
    response = signed_in_client.get(reverse("iam:session_current"))

    assert response.status_code == HTTPStatus.OK
    assert response["Content-Type"] == "application/json"
    assert response.json() == {
        "email": identity.email.value,
        "display_name": identity.display_name.value,
    }


def test_no_session_answers_the_not_authenticated_problem(
    client: Client, db: None
) -> None:
    response = client.get(reverse("iam:session_current"))

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/iam.not_authenticated",
        "status": 401,
    }
