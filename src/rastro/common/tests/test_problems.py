from http import HTTPStatus

import httpx


async def test_an_unknown_url_answers_a_not_found_problem(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.get("/nope")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {"type": "request.not_found", "status": 404}


async def test_a_wrong_method_answers_a_method_not_allowed_problem_with_allow(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.get("/sample/notes")

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["allow"] == "POST"
    assert response.json() == {"type": "request.method_not_allowed", "status": 405}


async def test_an_unexpected_exception_answers_an_internal_error_problem(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.get("/sample/boom")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {"type": "server.internal_error", "status": 500}


async def test_a_rastro_error_answers_the_problem_of_its_code_and_status(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.post("/sample/notes/rejected")

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {"type": "common_sample.note_rejected", "status": 409}
