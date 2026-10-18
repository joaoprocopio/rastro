from http import HTTPStatus

from django.test import Client
from django.urls import reverse


def test_sets_a_csrf_cookie_that_javascript_can_read(client: Client) -> None:
    response = client.get(reverse("iam:csrf_get"))

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    cookie = response.cookies["csrftoken"]
    assert cookie.value
    assert not cookie["httponly"]
