from http import HTTPStatus

import httpx
import pytest

from rastro.common.domain.value_objects import TokenBytes
from rastro.common.presentation.csrf import CsrfToken
from rastro.settings import Settings

PATH = "/sample/csrf"
CSRF_FAILED = {"type": "request.csrf_failed", "status": 403}


async def test_a_matching_token_passes(sample_client: httpx.AsyncClient) -> None:
    response = await sample_client.post(PATH)

    assert response.status_code == HTTPStatus.NO_CONTENT


async def test_a_post_without_the_header_fails(
    sample_client: httpx.AsyncClient,
    settings: Settings,
) -> None:
    del sample_client.headers[settings.csrf_header_name]

    response = await sample_client.post(PATH)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json() == CSRF_FAILED


async def test_a_header_that_differs_from_the_cookie_fails(
    sample_client: httpx.AsyncClient,
    settings: Settings,
) -> None:
    response = await sample_client.post(
        PATH, headers={settings.csrf_header_name: "other"}
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


async def test_a_post_without_the_cookie_fails(
    sample_client: httpx.AsyncClient,
    settings: Settings,
) -> None:
    sample_client.cookies.delete(settings.csrf_cookie_name)

    response = await sample_client.post(PATH)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


async def test_an_empty_cookie_and_an_empty_header_fail(
    sample_client: httpx.AsyncClient,
    settings: Settings,
) -> None:
    sample_client.cookies.set(settings.csrf_cookie_name, "")
    sample_client.headers[settings.csrf_header_name] = ""

    response = await sample_client.post(PATH)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


async def test_a_header_with_a_character_outside_ascii_fails(
    sample_client: httpx.AsyncClient,
    settings: Settings,
) -> None:
    response = await sample_client.post(
        PATH, headers={settings.csrf_header_name.encode(): "tökén".encode()}
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE"])
async def test_every_other_method_that_changes_state_needs_the_token(
    sample_client: httpx.AsyncClient, settings: Settings, method: str
) -> None:
    del sample_client.headers[settings.csrf_header_name]

    response = await sample_client.request(method, PATH)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == CSRF_FAILED


@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
async def test_a_safe_method_needs_no_token(
    sample_client: httpx.AsyncClient, settings: Settings, method: str
) -> None:
    del sample_client.headers[settings.csrf_header_name]
    sample_client.cookies.delete(settings.csrf_cookie_name)

    response = await sample_client.request(method, PATH)

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_a_csrf_token_of_16_bytes_has_22_characters() -> None:
    token = CsrfToken.generate(nbytes=TokenBytes(16))

    assert len(token.root.get_secret_value()) == 22


def test_a_csrf_token_hides_its_value_in_repr() -> None:
    token = CsrfToken.model_validate("abc123")

    assert "**********" in repr(token)
    assert "abc123" not in repr(token)
