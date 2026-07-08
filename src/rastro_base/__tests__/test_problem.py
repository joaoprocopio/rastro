import json
from http import HTTPStatus

import pydantic

from rastro_base.error import BaseError
from rastro_base.problem import (
    Problem,
    ProblemMapper,
    ValidationErrorMapper,
)
from rastro_base.pydantic import BaseModel


class _SampleError(BaseError):
    code = "SAMPLE_ERROR"
    status = HTTPStatus.NOT_FOUND
    title = "Sample error"


def test_problem_detail_serializes_reserved_members() -> None:
    problem = Problem(
        code="SAMPLE_ERROR",
        status=HTTPStatus.NOT_FOUND,
        title="Sample error",
        detail="not here",
    )

    assert problem.model_dump() == {
        "code": "SAMPLE_ERROR",
        "status": 404,
        "title": "Sample error",
        "detail": "not here",
    }


def test_problem_detail_omits_detail_when_absent() -> None:
    problem = Problem(
        code="SAMPLE_ERROR",
        status=HTTPStatus.NOT_FOUND,
        title="Sample error",
    )

    assert "detail" not in problem.model_dump()


def test_problem_detail_spreads_extensions_at_top_level() -> None:
    problem = Problem(
        code="SAMPLE_ERROR",
        status=HTTPStatus.NOT_FOUND,
        title="Sample error",
        detail="not here",
        extensions={"resource": "conta", "id": 7},
    )

    dumped = problem.model_dump()

    assert dumped["resource"] == "conta"
    assert dumped["id"] == 7
    assert "extensions" not in dumped


def test_problem_detail_mapper_maps_base_error() -> None:
    error = _SampleError(detail="conta not found", extensions={"id": 7})

    problem = ProblemMapper.map(error)

    assert problem.model_dump() == {
        "code": "SAMPLE_ERROR",
        "status": 404,
        "title": "Sample error",
        "detail": "conta not found",
        "id": 7,
    }


class _ValidatedInput(BaseModel):
    age: int


def _validation_error() -> pydantic.ValidationError:
    try:
        _ValidatedInput(age="not-a-number")
    except pydantic.ValidationError as exc:
        return exc
    raise AssertionError("expected a ValidationError")


def test_validation_error_mapper_maps_to_422() -> None:
    problem = ValidationErrorMapper.map(_validation_error())

    dumped = problem.model_dump()

    assert dumped["code"] == "VALIDATION_ERROR"
    assert dumped["status"] == 422
    assert "errors" in dumped


def test_validation_error_mapper_output_is_json_serializable() -> None:
    problem = ValidationErrorMapper.map(_validation_error())

    # must not raise — the pydantic error list has to be JSON-safe
    json.dumps(problem.model_dump())


def test_validation_error_mapper_handles_non_json_safe_input() -> None:
    # a malformed (non-JSON) request body surfaces the raw bytes as `input`;
    # the mapper must still produce a JSON-serializable body, not crash.
    try:
        _ValidatedInput.model_validate_json(b"not valid json")
    except pydantic.ValidationError as exc:
        problem = ValidationErrorMapper.map(exc)

    json.dumps(problem.model_dump())
