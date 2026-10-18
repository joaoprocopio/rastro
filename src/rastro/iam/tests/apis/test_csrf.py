from http import HTTPStatus

from django.test import Client

CSRF_URL = "/api/v1/iam/csrf"


def test_sets_a_csrf_cookie_that_javascript_can_read(client: Client) -> None:
    response = client.get(CSRF_URL)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    cookie = response.cookies["csrftoken"]
    assert cookie.value
    assert not cookie["httponly"]
