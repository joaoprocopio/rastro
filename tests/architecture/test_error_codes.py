import re
from http import HTTPStatus

import pytest

from rastro.app import ERROR_STATUSES
from rastro.common.domain.errors import BaseError
from rastro.common.tests.sample.presentation.views import (
    ERROR_STATUSES as SAMPLE_ERROR_STATUSES,
)
from tests.architecture.rules import error_classes, status_violations

CODE_FORM = re.compile(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*")
STATUSES = {**ERROR_STATUSES, **SAMPLE_ERROR_STATUSES}


def test_every_error_code_has_the_form_prefix_dot_name() -> None:
    codes = [error.code for error in error_classes()]

    assert [code for code in codes if not CODE_FORM.fullmatch(code)] == []


def test_every_error_has_a_row_in_an_error_to_status_table() -> None:
    assert status_violations(error_classes(), STATUSES) == []


def test_the_check_names_an_error_without_a_row() -> None:
    class WallCrackedError(BaseError):
        code = "tests.wall_cracked"

    assert status_violations([WallCrackedError], STATUSES) == [
        f"{__name__}.{WallCrackedError.__qualname__}: no row in an error-to-status table"
    ]


def test_every_error_answers_the_status_of_the_contract() -> None:
    assert {error.code: STATUSES[error] for error in error_classes()} == {
        "auth.email_in_use": 409,
        "auth.incorrect_credentials": 401,
        "auth.not_authenticated": 401,
        "common_sample.note_rejected": 409,
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
    }


def test_an_error_without_a_code_is_rejected() -> None:
    with pytest.raises(TypeError, match="WallPaintError declares no code"):

        class WallPaintError(BaseError):
            pass


def test_an_error_that_declares_a_status_is_rejected() -> None:
    with pytest.raises(TypeError, match="WallPaintError declares a status"):

        class WallPaintError(BaseError):
            code = "tests.wall_paint"
            status = HTTPStatus.CONFLICT


def test_an_error_that_repeats_a_code_is_rejected_with_both_classes_named() -> None:
    class BookingTakenError(BaseError):
        code = "tests.booking_taken"

    with pytest.raises(TypeError) as excinfo:

        class SeatTakenError(BaseError):
            code = "tests.booking_taken"

    message = str(excinfo.value)
    assert "SeatTakenError" in message
    assert "BookingTakenError" in message
    assert "tests.booking_taken" in message
