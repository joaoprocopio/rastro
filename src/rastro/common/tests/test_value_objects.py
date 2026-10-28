import pydantic
import pytest

from rastro.common.domain.value_objects import CorsOrigin, Id, TokenBytes
from rastro.common.tests.sample.application.dtos import PaintApplyInput
from rastro.common.tests.sample.domain.value_objects import Color


def test_a_value_object_strips_the_whitespace_around_its_value() -> None:
    assert Color("  red ").root == "red"


@pytest.mark.parametrize("value", ["re", "magenta", "Green", "r3d", ""])
def test_a_value_object_rejects_a_value_that_breaks_its_rules(value: str) -> None:
    with pytest.raises(pydantic.ValidationError):
        Color(value)


def test_a_rejection_never_shows_the_input() -> None:
    with pytest.raises(pydantic.ValidationError) as excinfo:
        Color("Secret")

    assert "Secret" not in str(excinfo.value)


def test_a_value_object_is_frozen_and_equal_by_value() -> None:
    color = Color("red")

    with pytest.raises(pydantic.ValidationError):
        color.root = "blue"  # type: ignore[misc]
    assert {color, Color("red")} == {Color("red")}


def test_model_validate_accepts_a_raw_value_or_a_built_value_object() -> None:
    assert Color.model_validate("red") == Color.model_validate(Color("red"))


def test_a_dto_parses_its_json_into_value_objects_and_dumps_it_back() -> None:
    paint = PaintApplyInput.model_validate_json('{"color": " red", "coats": 2}')

    assert paint.color == Color("red")
    assert paint.model_dump(mode="json") == {"color": "red", "coats": 2, "walls": None}


def test_a_dto_rejects_an_unknown_field() -> None:
    with pytest.raises(pydantic.ValidationError):
        PaintApplyInput.model_validate({"color": "red", "coats": 2, "brush": 1})


def test_an_id_accepts_a_positive_integer() -> None:
    assert Id(1).root == 1


@pytest.mark.parametrize("value", [0, -1, "1", True])
def test_an_id_rejects_a_value_that_is_not_a_positive_integer(value: object) -> None:
    with pytest.raises(pydantic.ValidationError):
        Id.model_validate(value)


def test_token_bytes_allows_16_bytes() -> None:
    assert TokenBytes(16).root == 16


def test_token_bytes_rejects_15_bytes() -> None:
    with pytest.raises(pydantic.ValidationError):
        TokenBytes(15)


@pytest.mark.parametrize(
    "value",
    [
        "http://localhost:5173",
        "https://rastro.example",
        "https://app.rastro-example.com:8443",
        "http://127.0.0.1:1",
        "https://x:65535",
        "http://x:443",
        "https://x:80",
        "http://[::1]:5173",
    ],
)
def test_a_cors_origin_accepts_a_scheme_a_host_and_an_optional_port(
    value: str,
) -> None:
    assert CorsOrigin(value).root == value


@pytest.mark.parametrize(
    "value",
    [
        "localhost:5173",
        "ftp://localhost",
        "http://localhost:5173/",
        "http://localhost/app",
        "http://Localhost",
        "HTTP://localhost",
        "http://",
        "http://..",
        "http://localhost.",
        "http://.localhost",
        "http://a..b",
        "http://-a.b",
        "http://a-.b",
        "http://localhost:",
        "http://localhost:0",
        "http://localhost:05173",
        "http://localhost:65536",
        "http://localhost:99999",
        "http://x:80",
        "https://x:443",
        "http://[]",
        "http://[::1",
        "http://[::g]",
        "http://[::1]:80",
    ],
)
def test_a_cors_origin_rejects_a_value_that_no_browser_sends_as_origin(
    value: str,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        CorsOrigin(value)
