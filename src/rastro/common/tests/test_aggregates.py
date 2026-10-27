import pydantic
import pytest

from rastro.common.tests.sample.domain.aggregates import Note
from rastro.common.tests.sample.domain.value_objects import Color


def test_an_aggregate_changes_a_field_by_assignment() -> None:
    note = Note(id=1, color=Color("red"))

    note.color = Color("blue")

    assert note == Note(id=1, color=Color("blue"))


def test_an_aggregate_rejects_an_assignment_that_breaks_its_types() -> None:
    note = Note(id=1, color=Color("red"))

    with pytest.raises(pydantic.ValidationError):
        note.id = "2"  # type: ignore[assignment]


def test_two_aggregates_are_equal_only_when_every_field_is_equal() -> None:
    assert Note(id=1, color=Color("red")) == Note(id=1, color=Color("red"))
    assert Note(id=1, color=Color("red")) != Note(id=1, color=Color("blue"))
