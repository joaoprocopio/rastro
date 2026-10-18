from http import HTTPStatus

from django.test import Client
from django.urls import reverse


def test_ends_the_session(signed_in_client: Client) -> None:
    session_url = reverse("iam:session_current")
    assert signed_in_client.get(session_url).status_code == HTTPStatus.OK

    response = signed_in_client.post(reverse("iam:session_end"))

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert signed_in_client.get(session_url).status_code == HTTPStatus.UNAUTHORIZED


def test_succeeds_without_a_session(client: Client, db: None) -> None:
    response = client.post(reverse("iam:session_end"))

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
