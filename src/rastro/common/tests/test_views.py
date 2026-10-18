import json
from http import HTTPStatus

import pytest
from django.test import Client

SAMPLE_URLS = "rastro.common.tests.sample.urls"


@pytest.mark.urls(SAMPLE_URLS)
def test_a_csrf_failure_is_a_problem_403() -> None:
    client = Client(enforce_csrf_checks=True)

    response = client.post(
        "/paint",
        data=json.dumps({"color": "red", "coats": 2}),
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "/problems/request.csrf_failed", "status": 403}


def test_an_unknown_url_is_a_problem_404_without_a_type(client: Client) -> None:
    response = client.get("/nope")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"status": 404}


@pytest.mark.urls(SAMPLE_URLS)
def test_an_unhandled_exception_is_a_problem_500_without_a_type() -> None:
    client = Client(raise_request_exception=False)

    response = client.get("/boom")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"status": 500}
