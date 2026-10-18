import json
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from django.test import Client

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

pytestmark = pytest.mark.urls("rastro.common.tests.sample.urls")

PAINT_URL = "/paint"
PAINT_COUNT_URL = "/paint/count"


def _post_json(
    client: Client, url: str, payload: object
) -> "_MonkeyPatchedWSGIResponse":
    return client.post(url, data=json.dumps(payload), content_type="application/json")


def test_parses_the_body_and_answers_with_the_output(client: Client) -> None:
    response = _post_json(client, PAINT_URL, {"color": "red", "coats": 2})

    assert response.status_code == HTTPStatus.OK
    assert response["Content-Type"] == "application/json"
    assert response.json() == {"color": "red", "coats": 2}


def test_a_missing_field_is_a_validation_failure(client: Client) -> None:
    response = _post_json(client, PAINT_URL, {"color": "red"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/coats", "type": "/problems/request.field_required"},
        ],
    }


def test_a_wrong_type_is_a_validation_failure(client: Client) -> None:
    response = _post_json(client, PAINT_URL, {"color": "red", "coats": "two"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["errors"] == [
        {"pointer": "#/coats", "type": "/problems/request.invalid_type"},
    ]


def test_malformed_json_is_a_validation_failure(client: Client) -> None:
    response = client.post(
        PAINT_URL, data="{not valid", content_type="application/json"
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#", "type": "/problems/request.invalid_json"}],
    }


def test_an_unknown_field_is_a_validation_failure(client: Client) -> None:
    response = _post_json(client, PAINT_URL, {"color": "red", "coats": 2, "brush": 1})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["errors"] == [
        {"pointer": "#/brush", "type": "/problems/request.unknown_field"},
    ]


def test_an_invalid_value_object_carries_its_own_code(client: Client) -> None:
    response = _post_json(client, PAINT_URL, {"color": "green", "coats": 2})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["errors"] == [
        {"pointer": "#/color", "type": "/problems/sample.invalid_color"},
    ]


def test_every_field_error_appears_in_one_response(client: Client) -> None:
    response = _post_json(client, PAINT_URL, {"color": "green", "brush": 1})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["errors"] == [
        {"pointer": "#/brush", "type": "/problems/request.unknown_field"},
        {"pointer": "#/color", "type": "/problems/sample.invalid_color"},
        {"pointer": "#/coats", "type": "/problems/request.field_required"},
    ]


def test_a_problem_carries_no_title_detail_or_code(client: Client) -> None:
    response = _post_json(client, PAINT_URL, {})

    assert set(response.json()) == {"type", "status", "errors"}


def test_require_post_answers_a_get_with_a_problem_405(client: Client) -> None:
    response = client.get(PAINT_URL)

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response["Content-Type"] == "application/problem+json"
    assert response["Allow"] == "POST"
    assert response.json() == {"status": 405}


def test_require_get_answers_a_post_with_a_problem_405(client: Client) -> None:
    response = client.post(PAINT_COUNT_URL)

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response["Content-Type"] == "application/problem+json"
    assert response["Allow"] == "GET"
    assert response.json() == {"status": 405}


def test_respond_without_an_output_has_no_body(client: Client) -> None:
    response = client.get(PAINT_COUNT_URL)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""


def test_a_csrf_failure_is_a_problem_403() -> None:
    client = Client(enforce_csrf_checks=True)

    response = client.post(
        PAINT_URL,
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


def test_an_unhandled_exception_is_a_problem_500_without_a_type() -> None:
    client = Client(raise_request_exception=False)

    response = client.get("/boom")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"status": 500}
