import pydantic
import pytest

from rastro.common.tests.sample.values import Color
from rastro.common.values import InvalidValueError


class Paint(pydantic.BaseModel):
    color: Color


def test_parses_a_json_string_into_the_value_object() -> None:
    paint = Paint.model_validate_json('{"color": "red"}')

    assert paint.color == Color("red")
    assert paint.color.value == "red"


def test_serializes_back_to_a_plain_string() -> None:
    paint = Paint(color=Color("blue"))

    assert paint.model_dump() == {"color": "blue"}
    assert paint.model_dump_json() == '{"color":"blue"}'


def test_reports_an_invalid_value_as_a_field_error_with_its_code() -> None:
    with pytest.raises(pydantic.ValidationError) as excinfo:
        Paint.model_validate_json('{"color": "green"}')

    [error] = excinfo.value.errors()
    assert error["loc"] == ("color",)
    assert error["type"] == "value_error"
    assert error["ctx"]["error"].code == "sample.invalid_color"


def test_rejects_a_non_string_as_a_type_error_before_the_value_object_runs() -> None:
    with pytest.raises(pydantic.ValidationError) as excinfo:
        Paint.model_validate_json('{"color": 1}')

    [error] = excinfo.value.errors()
    assert error["loc"] == ("color",)
    assert error["type"] == "string_type"


def test_the_code_is_readable_outside_pydantic() -> None:
    with pytest.raises(InvalidValueError) as excinfo:
        Color("green")

    assert excinfo.value.code == "sample.invalid_color"
    assert isinstance(excinfo.value, ValueError)
