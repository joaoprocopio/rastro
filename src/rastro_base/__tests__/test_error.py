# invariants, now enforced structurally rather than by a runtime registry:
# - a concrete subclass MUST supply `code`, `status` and `title`; the members
#   are abstract, so omitting any one makes the class impossible to instantiate
#   (`ABCMeta` raises `TypeError`, and the type checker flags the call site)
# - `code`/`status`/`title` are plain `str`/`int`/`str`; the framework is
#   domain-agnostic, so the code catalog is owned by the application layer
# instance data (RFC 7807, per-occurrence):
# - `detail` is optional
# - `extensions` is optional


from http import HTTPStatus

import pytest

from rastro_base.error import BaseError


class _CompleteError(BaseError):
    code = "COMPLETE_ERROR"
    status = HTTPStatus.NOT_FOUND
    title = "Complete"


def test_complete_subclass_can_be_instantiated_and_exposes_members() -> None:
    error = _CompleteError(detail="boom", extensions={"foo": "bar"})

    assert error.code == "COMPLETE_ERROR"
    assert error.status == HTTPStatus.NOT_FOUND
    assert error.title == "Complete"
    assert error.detail == "boom"
    assert error.extensions is not None
    assert error.extensions["foo"] == "bar"


def test_extensions_default_to_none() -> None:
    error = _CompleteError(detail="boom")

    assert error.extensions is None


def test_subclass_missing_code_cannot_be_instantiated() -> None:
    class _NoCode(BaseError):
        status = HTTPStatus.BAD_REQUEST
        title = "No code"

    with pytest.raises(TypeError):
        _NoCode()  # type: ignore[abstract]


def test_subclass_missing_status_cannot_be_instantiated() -> None:
    class _NoStatus(BaseError):
        code = "SOME_CODE"
        title = "No status"

    with pytest.raises(TypeError):
        _NoStatus()  # type: ignore[abstract]


def test_subclass_missing_title_cannot_be_instantiated() -> None:
    class _NoTitle(BaseError):
        code = "SOME_CODE"
        status = HTTPStatus.BAD_REQUEST

    with pytest.raises(TypeError):
        _NoTitle()  # type: ignore[abstract]
