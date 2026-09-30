import enum
from http import HTTPStatus

import pytest

from rastro.exceptions import BaseError, ErrorCode


class _CompleteError(BaseError):
    code = ErrorCode.BASE_HTTP_ERROR
    status = HTTPStatus.NOT_FOUND
    title = "Complete"


def test_complete_subclass_can_be_instantiated_and_exposes_members() -> None:
    error = _CompleteError(detail="boom", extensions={"foo": "bar"})

    assert error.code == ErrorCode.BASE_HTTP_ERROR
    assert error.status == HTTPStatus.NOT_FOUND
    assert error.title == "Complete"
    assert error.detail == "boom"
    assert error.extensions == {"foo": "bar"}
    assert str(error) == "boom"


def test_extensions_default_to_none() -> None:
    assert _CompleteError(detail="boom").extensions is None


def test_subclass_missing_code_cannot_be_instantiated() -> None:
    class _NoCode(BaseError):
        status = HTTPStatus.BAD_REQUEST
        title = "No code"

    with pytest.raises(TypeError, match="code"):
        _NoCode()


def test_subclass_missing_status_cannot_be_instantiated() -> None:
    class _NoStatus(BaseError):
        code = ErrorCode.BASE_HTTP_ERROR
        title = "No status"

    with pytest.raises(TypeError, match="status"):
        _NoStatus()


def test_subclass_missing_title_cannot_be_instantiated() -> None:
    class _NoTitle(BaseError):
        code = ErrorCode.BASE_HTTP_ERROR
        status = HTTPStatus.BAD_REQUEST

    with pytest.raises(TypeError, match="title"):
        _NoTitle()


def test_every_code_value_matches_its_name() -> None:
    for code in ErrorCode:
        assert code.value == code.name


def test_unique_decorator_rejects_duplicate_values() -> None:
    # documents the guarantee `@enum.unique` gives the catalog: a duplicate
    # value is a definition-time error, not a silent alias
    with pytest.raises(ValueError, match="duplicate"):

        @enum.unique
        class _Dup(enum.StrEnum):
            ONE = "SAME"
            TWO = "SAME"
