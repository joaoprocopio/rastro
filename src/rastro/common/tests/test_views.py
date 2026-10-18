from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.urls("rastro.common.tests.sample.urls")


def test_parses_the_body_and_answers_with_the_output(client: Client) -> None:
    response = client.post(
        reverse("sample:paint_apply"),
        {"color": "red", "coats": 2},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.OK
    assert response["Content-Type"] == "application/json"
    assert response.json() == {"color": "red", "coats": 2}


def test_a_missing_field_is_a_validation_failure(client: Client) -> None:
    response = client.post(
        reverse("sample:paint_apply"), {"color": "red"}, content_type="application/json"
    )

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
    response = client.post(
        reverse("sample:paint_apply"),
        {"color": "red", "coats": "two"},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["errors"] == [
        {"pointer": "#/coats", "type": "/problems/request.invalid_type"},
    ]


def test_malformed_json_is_a_validation_failure(client: Client) -> None:
    response = client.post(
        reverse("sample:paint_apply"), "{not valid", content_type="application/json"
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#", "type": "/problems/request.invalid_json"}],
    }


def test_an_unknown_field_is_a_validation_failure(client: Client) -> None:
    response = client.post(
        reverse("sample:paint_apply"),
        {"color": "red", "coats": 2, "brush": 1},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["errors"] == [
        {"pointer": "#/brush", "type": "/problems/request.unknown_field"},
    ]


@pytest.mark.parametrize(
    ("color", "item"),
    [
        ("Green", {"pointer": "#/color", "type": "/problems/request.invalid_format"}),
        (
            "re",
            {
                "pointer": "#/color",
                "type": "/problems/request.too_short",
                "min_length": 3,
            },
        ),
        (
            "magenta",
            {
                "pointer": "#/color",
                "type": "/problems/request.too_long",
                "max_length": 6,
            },
        ),
    ],
)
def test_a_value_object_rule_names_the_rule_and_its_limit(
    client: Client, color: str, item: dict[str, object]
) -> None:
    response = client.post(
        reverse("sample:paint_apply"),
        {"color": color, "coats": 2},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "type": "/problems/request.validation_failed",
        "status": 422,
        "errors": [item],
    }


def test_every_field_error_appears_in_one_response(client: Client) -> None:
    response = client.post(
        reverse("sample:paint_apply"),
        {"color": "Green", "brush": 1},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["errors"] == [
        {"pointer": "#/brush", "type": "/problems/request.unknown_field"},
        {"pointer": "#/color", "type": "/problems/request.invalid_format"},
        {"pointer": "#/coats", "type": "/problems/request.field_required"},
    ]


def test_a_problem_carries_no_title_detail_or_code(client: Client) -> None:
    response = client.post(
        reverse("sample:paint_apply"), {}, content_type="application/json"
    )

    assert set(response.json()) == {"type", "status", "errors"}


def test_require_post_answers_a_get_with_a_problem_405(client: Client) -> None:
    response = client.get(reverse("sample:paint_apply"))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response["Content-Type"] == "application/problem+json"
    assert response["Allow"] == "POST"
    assert response.json() == {
        "type": "/problems/request.method_not_allowed",
        "status": 405,
    }


def test_require_get_answers_a_post_with_a_problem_405(client: Client) -> None:
    response = client.post(reverse("sample:paint_count"))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response["Content-Type"] == "application/problem+json"
    assert response["Allow"] == "GET"
    assert response.json() == {
        "type": "/problems/request.method_not_allowed",
        "status": 405,
    }


def test_respond_without_an_output_has_no_body(client: Client) -> None:
    response = client.get(reverse("sample:paint_count"))

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""


def test_a_csrf_failure_is_a_problem_403() -> None:
    client = Client(enforce_csrf_checks=True)

    response = client.post(
        reverse("sample:paint_apply"),
        {"color": "red", "coats": 2},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "/problems/request.csrf_failed", "status": 403}


def test_an_unknown_url_is_a_problem_404(client: Client) -> None:
    response = client.get("/nope")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "/problems/request.not_found", "status": 404}


def test_an_http404_from_a_view_is_the_same_problem_404(client: Client) -> None:
    response = client.get(reverse("sample:paint_find"))

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {"type": "/problems/request.not_found", "status": 404}


def test_an_unhandled_exception_is_a_problem_500() -> None:
    client = Client(raise_request_exception=False)

    response = client.get(reverse("sample:boom_raise"))

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/server.internal_error",
        "status": 500,
    }


@pytest.mark.django_db
def test_a_check_constraint_violation_is_a_problem_500() -> None:
    client = Client(raise_request_exception=False)

    response = client.post(reverse("sample:wall_paint"))

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response["Content-Type"] == "application/problem+json"
    assert response.json() == {
        "type": "/problems/server.internal_error",
        "status": 500,
    }
