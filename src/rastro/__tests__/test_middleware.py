import json
from http import HTTPStatus

import pydantic
from django.http import HttpResponse
from django.test import RequestFactory

from rastro.middleware import ExceptionHandlerMiddleware
from rastro_base.error import BaseError
from rastro_base.pydantic import BaseModel


class _AccountNotFoundError(BaseError):
    code = "TEST_MW_ACCOUNT_NOT_FOUND"
    status = HTTPStatus.NOT_FOUND
    title = "Account not found"


def _middleware() -> ExceptionHandlerMiddleware:
    return ExceptionHandlerMiddleware(lambda request: HttpResponse())


def test_base_error_becomes_problem_json() -> None:
    request = RequestFactory().get("/")
    error = _AccountNotFoundError(
        detail="No account found.", extensions={"email": "a@b.com"}
    )

    response = _middleware().process_exception(request, error)

    assert response is not None
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response["Content-Type"] == "application/problem+json"
    assert json.loads(response.content) == {
        "code": "TEST_MW_ACCOUNT_NOT_FOUND",
        "status": 404,
        "title": "Account not found",
        "detail": "No account found.",
        "email": "a@b.com",
    }


def test_validation_error_becomes_problem_json() -> None:
    class _Input(BaseModel):
        age: int

    request = RequestFactory().post("/")
    try:
        _Input(age="nope")
    except pydantic.ValidationError as exc:
        response = _middleware().process_exception(request, exc)

    assert response is not None
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response["Content-Type"] == "application/problem+json"
    body = json.loads(response.content)
    assert body["code"] == "BASE_VALIDATION_ERROR"
    assert "errors" in body


def test_unhandled_exception_passes_through() -> None:
    request = RequestFactory().get("/")

    response = _middleware().process_exception(request, ValueError("boom"))

    assert response is None
