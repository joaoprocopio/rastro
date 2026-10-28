from http import HTTPStatus

import httpx
import pytest


async def test_a_valid_body_reaches_the_view(sample_client: httpx.AsyncClient) -> None:
    response = await sample_client.post(
        "/sample/paints", json={"color": "red", "coats": 2}
    )

    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.parametrize(
    ("color", "item"),
    [
        ("re", {"pointer": "#/color", "type": "request.too_short", "min_length": 3}),
        (
            "magenta",
            {"pointer": "#/color", "type": "request.too_long", "max_length": 6},
        ),
        ("Green", {"pointer": "#/color", "type": "request.invalid_format"}),
    ],
)
async def test_a_value_object_rule_answers_its_item_with_its_data(
    sample_client: httpx.AsyncClient, color: str, item: dict[str, object]
) -> None:
    response = await sample_client.post(
        "/sample/paints", json={"color": color, "coats": 2}
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [item],
    }


async def test_malformed_json_answers_an_invalid_json_item_at_the_root(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.post(
        "/sample/paints",
        content=b'{"color": "red",',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#", "type": "request.invalid_json"}],
    }


async def test_a_missing_body_answers_a_field_required_item_at_the_root(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.post("/sample/paints")

    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#", "type": "request.field_required"}],
    }


async def test_a_body_that_is_no_object_answers_an_invalid_type_item_at_the_root(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.post("/sample/paints", json=["red", 2])

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [{"pointer": "#", "type": "request.invalid_type"}],
    }


async def test_every_failed_field_answers_its_own_item(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.post(
        "/sample/paints", json={"coats": "two", "brush": 1}
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "type": "request.validation_failed",
        "status": 422,
        "errors": [
            {"pointer": "#/color", "type": "request.field_required"},
            {"pointer": "#/coats", "type": "request.invalid_type"},
            {"pointer": "#/brush", "type": "request.unknown_field"},
        ],
    }


async def test_a_validation_failure_never_shows_the_input(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.post(
        "/sample/paints", json={"color": "Secret", "coats": "hidden"}
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "Secret" not in response.text
    assert "hidden" not in response.text


async def test_a_pydantic_error_type_with_no_case_answers_an_internal_error(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.post(
        "/sample/paints", json={"color": "red", "coats": 0}
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {"type": "server.internal_error", "status": 500}
