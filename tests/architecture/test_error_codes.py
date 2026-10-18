import importlib
import importlib.util
import re
from http import HTTPStatus
from types import ModuleType

import pytest
from django.apps import apps

from rastro.common import errors as common_errors
from rastro.common.errors import BaseError

CODE_FORM = re.compile(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*")


def _error_modules() -> list[ModuleType]:
    modules = [common_errors]
    for config in apps.get_app_configs():
        module_name = f"{config.name}.errors"
        if config.name.startswith("rastro.") and importlib.util.find_spec(module_name):
            modules.append(importlib.import_module(module_name))
    return modules


def _error_classes() -> list[type[BaseError]]:
    return [
        member
        for module in _error_modules()
        for member in vars(module).values()
        if isinstance(member, type)
        and issubclass(member, BaseError)
        and member is not BaseError
        and member.__module__ == module.__name__
    ]


def test_every_error_code_has_the_form_prefix_dot_name() -> None:
    codes = [error.code for error in _error_classes()]

    assert [code for code in codes if not CODE_FORM.fullmatch(code)] == []


def test_every_error_declares_the_code_and_status_of_the_contract() -> None:
    assert {error.code: error.status for error in _error_classes()} == {
        "request.validation_failed": 422,
        "request.field_required": 422,
        "request.invalid_type": 422,
        "request.invalid_json": 422,
        "request.unknown_field": 422,
        "request.too_short": 422,
        "request.too_long": 422,
        "request.invalid_format": 422,
        "request.csrf_failed": 403,
        "request.not_found": 404,
        "request.method_not_allowed": 405,
        "server.internal_error": 500,
        "iam.email_in_use": 409,
        "iam.incorrect_credentials": 401,
        "iam.not_authenticated": 401,
    }


def test_an_error_without_a_code_is_rejected() -> None:
    with pytest.raises(TypeError, match="WallPaintError declares no code"):

        class WallPaintError(BaseError):
            status = HTTPStatus.CONFLICT


def test_an_error_without_a_status_is_rejected() -> None:
    with pytest.raises(TypeError, match="WallPaintError declares no status"):

        class WallPaintError(BaseError):
            code = "tests.wall_paint"


def test_an_error_that_repeats_a_code_is_rejected_with_both_classes_named() -> None:
    class BookingTakenError(BaseError):
        code = "tests.booking_taken"
        status = HTTPStatus.CONFLICT

    with pytest.raises(TypeError) as excinfo:

        class SeatTakenError(BaseError):
            code = "tests.booking_taken"
            status = HTTPStatus.CONFLICT

    message = str(excinfo.value)
    assert "SeatTakenError" in message
    assert "BookingTakenError" in message
    assert "tests.booking_taken" in message
