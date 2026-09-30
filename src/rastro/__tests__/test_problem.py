from http import HTTPStatus

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rastro.exceptions import BaseError, ErrorCode
from rastro.problem import PROBLEM_MEDIA_TYPE, Problem, install_exception_handlers


class _AccountNotFoundError(BaseError):
    code = ErrorCode.BASE_HTTP_ERROR
    status = HTTPStatus.NOT_FOUND
    title = "Account not found"


def test_problem_serializes_reserved_members() -> None:
    problem = Problem(
        code="SAMPLE_ERROR", status=404, title="Sample error", detail="not here"
    )

    assert problem.model_dump() == {
        "code": "SAMPLE_ERROR",
        "status": 404,
        "title": "Sample error",
        "detail": "not here",
    }


def test_problem_omits_detail_when_absent() -> None:
    problem = Problem(code="SAMPLE_ERROR", status=404, title="Sample error")

    assert "detail" not in problem.model_dump()


def test_problem_spreads_extensions_at_top_level() -> None:
    problem = Problem(
        code="SAMPLE_ERROR",
        status=404,
        title="Sample error",
        extensions={"resource": "account", "id": 7},
    )

    dumped = problem.model_dump()

    assert dumped["resource"] == "account"
    assert dumped["id"] == 7
    assert "extensions" not in dumped


def test_problem_extensions_never_overwrite_reserved_members() -> None:
    problem = Problem(
        code="SAMPLE_ERROR",
        status=404,
        title="Sample error",
        extensions={"status": 200, "type": "about:blank"},
    )

    dumped = problem.model_dump()

    assert dumped["status"] == 404
    assert "type" not in dumped


def test_problem_from_error() -> None:
    error = _AccountNotFoundError(detail="account not found", extensions={"id": 7})

    assert Problem.from_error(error).model_dump() == {
        "code": "BASE_HTTP_ERROR",
        "status": 404,
        "title": "Account not found",
        "detail": "account not found",
        "id": 7,
    }


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    install_exception_handlers(app)

    @app.get("/base-error")
    def raise_base_error() -> None:
        raise _AccountNotFoundError("No account found.", extensions={"id": 7})

    @app.get("/unexpected")
    def raise_unexpected() -> None:
        raise RuntimeError("boom")

    @app.get("/typed/{number}")
    def typed(number: int) -> int:
        return number

    return TestClient(app, raise_server_exceptions=False)


def test_base_error_becomes_problem_json(client: TestClient) -> None:
    response = client.get("/base-error")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == PROBLEM_MEDIA_TYPE
    assert response.json() == {
        "code": "BASE_HTTP_ERROR",
        "status": 404,
        "title": "Account not found",
        "detail": "No account found.",
        "id": 7,
    }


def test_request_validation_error_becomes_problem_json(client: TestClient) -> None:
    response = client.get("/typed/not-a-number")

    body = response.json()
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.headers["content-type"] == PROBLEM_MEDIA_TYPE
    assert body["code"] == "BASE_VALIDATION_ERROR"
    assert body["errors"][0]["loc"] == ["path", "number"]
    assert "input" not in body["errors"][0]


def test_http_exception_becomes_problem_json(client: TestClient) -> None:
    response = client.get("/missing")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == PROBLEM_MEDIA_TYPE
    assert response.json() == {
        "code": "BASE_HTTP_ERROR",
        "status": 404,
        "title": "Not Found",
    }


def test_http_exception_keeps_its_headers(client: TestClient) -> None:
    response = client.post("/base-error")

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response.headers["allow"] == "GET"


def test_unexpected_error_becomes_opaque_problem_json(client: TestClient) -> None:
    response = client.get("/unexpected")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.headers["content-type"] == PROBLEM_MEDIA_TYPE
    assert response.json() == {
        "code": "BASE_INTERNAL_ERROR",
        "status": 500,
        "title": "Internal Server Error",
    }
