import pydantic
import pytest

from rastro.common.tests.sample.values import Color


class Paint(pydantic.BaseModel):
    color: Color


def test_parses_a_json_string_into_the_value_object() -> None:
    paint = Paint.model_validate_json('{"color": "red"}')

    assert paint.color == Color("red")
    assert paint.color.root == "red"


def test_serializes_back_to_a_plain_string() -> None:
    paint = Paint(color=Color("blue"))

    assert paint.model_dump() == {"color": "blue"}
    assert paint.model_dump_json() == '{"color":"blue"}'


def test_accepts_a_built_value_object() -> None:
    color = Color("red")

    assert Paint(color=color).color == color


def test_rejects_a_value_that_breaks_its_rule() -> None:
    with pytest.raises(pydantic.ValidationError):
        Color("Green")


def test_is_frozen_and_hashable() -> None:
    color = Color("red")

    with pytest.raises(pydantic.ValidationError):
        color.root = "blue"  # type: ignore[misc]
    assert {color, Color("red")} == {Color("red")}
