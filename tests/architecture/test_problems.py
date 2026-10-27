import ast
import inspect
import textwrap
from http import HTTPStatus
from typing import Any

import pydantic
import pytest

from rastro.common.application.dtos import DTO
from rastro.common.domain.errors import BaseError
from rastro.common.presentation.errors import ValidationItem
from rastro.common.presentation.problems import Problem


class LimitExtensions(DTO):
    max_length: int
    unit: str | None = None


class LimitReachedError(BaseError):
    code = "tests.limit_reached"

    def __init__(self, extensions: LimitExtensions) -> None:
        super().__init__(extensions)


def test_a_problem_serializes_its_extensions_at_the_top_level() -> None:
    problem = Problem.from_error(
        LimitReachedError(LimitExtensions(max_length=8)), status=HTTPStatus.CONFLICT
    )

    assert problem.model_dump(mode="json") == {
        "type": "tests.limit_reached",
        "status": 409,
        "max_length": 8,
    }


def test_a_problem_omits_the_rfc_members_that_have_no_value() -> None:
    problem = Problem(type="tests.limit_reached", status=HTTPStatus.CONFLICT)

    assert problem.model_dump(mode="json") == {
        "type": "tests.limit_reached",
        "status": 409,
    }


@pytest.mark.parametrize("name", ["type", "status", "title", "detail", "instance"])
def test_an_extension_named_after_an_rfc_member_is_rejected(name: str) -> None:
    fields: dict[str, Any] = {name: (int, ...)}
    extensions = pydantic.create_model("Extensions", __base__=DTO, **fields)

    with pytest.raises(ValueError, match=f"'{name}' is a member of Problem"):
        Problem(
            type="tests.limit_reached",
            status=HTTPStatus.CONFLICT,
            extensions=extensions(**{name: 1}),
        )


@pytest.mark.parametrize("name", ["ab", "max-length", "1limit", "límite"])
def test_an_extension_named_against_the_rfc_rule_is_rejected(name: str) -> None:
    fields: dict[str, Any] = {name: (int, ...)}
    extensions = pydantic.create_model("Extensions", __base__=DTO, **fields)

    with pytest.raises(ValueError, match="breaks the RFC 9457 naming rule"):
        Problem(
            type="tests.limit_reached",
            status=HTTPStatus.CONFLICT,
            extensions=extensions.model_validate({name: 1}),
        )


def test_from_error_has_no_match_on_error_classes() -> None:
    tree = ast.parse(textwrap.dedent(inspect.getsource(Problem.from_error)))

    assert [node for node in ast.walk(tree) if isinstance(node, ast.Match)] == []


@pytest.mark.parametrize("name", ["pointer", "type"])
def test_an_item_extension_named_after_an_item_member_is_rejected(name: str) -> None:
    fields: dict[str, Any] = {name: (int, ...)}
    extensions = pydantic.create_model("Extensions", __base__=DTO, **fields)

    with pytest.raises(ValueError, match=f"'{name}' is a member of ValidationItem"):
        ValidationItem(
            pointer="#/color",
            type="request.too_short",
            extensions=extensions(**{name: 1}),
        )


def test_neither_a_problem_nor_an_item_names_a_rule() -> None:
    assert set(Problem.model_fields) == {
        "type",
        "status",
        "title",
        "detail",
        "instance",
        "extensions",
    }
    assert set(ValidationItem.model_fields) == {"pointer", "type", "extensions"}
