from http import HTTPStatus

from django.db import connection
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
        "email": identity.email.root,
        "display_name": identity.display_name.root,
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


def test_an_email_that_fails_its_value_object_in_the_database_answers_the_internal_error_problem(
    signed_in_client: Client, identity: Identity
) -> None:
    signed_in_client.raise_request_exception = False
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {Identity._meta.db_table} SET email = %s WHERE id = %s",
            ["not-an-email", identity.pk],
        )

    response = signed_in_client.get(reverse("iam:session_current"))

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/server.internal_error",
        "status": 500,
    }
