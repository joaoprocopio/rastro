import json
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from django.test import Client

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

pytestmark = pytest.mark.urls("rastro.common.tests.sample.urls")

PAINT_URL = "/paint"


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
