from http import HTTPStatus

import httpx
import pytest

PATH = "/sample/csrf"
CSRF_COOKIE = "rastro_csrf"
CSRF_HEADER = "X-CSRF-Token"
CSRF_FAILED = {"type": "request.csrf_failed", "status": 403}


async def test_a_matching_token_passes(sample_client: httpx.AsyncClient) -> None:
    response = await sample_client.post(PATH)

    assert response.status_code == HTTPStatus.NO_CONTENT


async def test_a_post_without_the_header_fails(
    sample_client: httpx.AsyncClient,
) -> None:
    del sample_client.headers[CSRF_HEADER]

    response = await sample_client.post(PATH)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json() == CSRF_FAILED


async def test_a_header_that_differs_from_the_cookie_fails(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.post(PATH, headers={CSRF_HEADER: "other"})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


async def test_a_post_without_the_cookie_fails(
    sample_client: httpx.AsyncClient,
) -> None:
    sample_client.cookies.delete(CSRF_COOKIE)

    response = await sample_client.post(PATH)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


async def test_an_empty_cookie_and_an_empty_header_fail(
    sample_client: httpx.AsyncClient,
) -> None:
    sample_client.cookies.set(CSRF_COOKIE, "")
    sample_client.headers[CSRF_HEADER] = ""

    response = await sample_client.post(PATH)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


async def test_a_header_with_a_character_outside_ascii_fails(
    sample_client: httpx.AsyncClient,
) -> None:
    response = await sample_client.post(
        PATH, headers={CSRF_HEADER.encode(): "tökén".encode()}
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE"])
async def test_every_other_method_that_changes_state_needs_the_token(
    sample_client: httpx.AsyncClient, method: str
) -> None:
    del sample_client.headers[CSRF_HEADER]

    response = await sample_client.request(method, PATH)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
async def test_a_safe_method_needs_no_token(
    sample_client: httpx.AsyncClient, method: str
) -> None:
    del sample_client.headers[CSRF_HEADER]
    sample_client.cookies.delete(CSRF_COOKIE)

    response = await sample_client.request(method, PATH)

    assert response.status_code == HTTPStatus.NO_CONTENT
