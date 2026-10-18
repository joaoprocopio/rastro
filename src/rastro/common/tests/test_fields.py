from enum import StrEnum

import pytest
from django.core.exceptions import ValidationError
from django.db.migrations.writer import MigrationWriter

from rastro.common.fields import (
    StrEnumField,
    StrValueObjectField,
    str_enum_to_choices,
)
from rastro.common.tests.sample.models import Post, Status
from rastro.common.tests.sample.values import Color
from rastro.common.values import InvalidValueError


def test_str_enum_to_choices() -> None:
    class MockStatus(StrEnum):
        DRAFT = "draft"
        PUBLISHED = "published"

    choices = str_enum_to_choices(MockStatus)

    assert choices == [("draft", "DRAFT"), ("published", "PUBLISHED")]


@pytest.mark.django_db
def test_returns_the_enum_member_on_read() -> None:
    Post.objects.create(status=Status.PUBLISHED)

    post = Post.objects.get()

    assert post.status is Status.PUBLISHED


@pytest.mark.django_db
def test_rejects_an_unknown_value_on_write() -> None:
    with pytest.raises(ValueError):
        Post.objects.create(status="archived")  # type: ignore[misc]


def test_rejects_an_unknown_value_from_the_database() -> None:
    field = StrEnumField(Status)

    with pytest.raises(ValueError):
        field.from_db_value("archived", None, None)


def test_rejects_an_unknown_value_from_the_admin_as_a_validation_error() -> None:
    field = StrEnumField(Status)

    with pytest.raises(ValidationError) as excinfo:
        field.to_python("archived")

    assert excinfo.value.code == "invalid_choice"


def test_builds_its_choices_and_max_length_from_the_enum() -> None:
    field = StrEnumField(Status)

    assert field.choices == [("draft", "DRAFT"), ("published", "PUBLISHED")]
    assert field.max_length == len("published")


def test_deconstructs_to_a_migration_that_names_the_enum() -> None:
    field = StrEnumField(Status)

    _name, path, args, kwargs = field.deconstruct()
    serialized, imports = MigrationWriter.serialize(field)

    assert path == "rastro.common.fields.StrEnumField"
    assert args == []
    assert kwargs == {"enum": Status}
    assert "rastro.common.tests.sample.models.Status" in serialized
    assert "import rastro.common.tests.sample.models" in imports


def test_str_value_object_field_returns_the_value_object_on_read() -> None:
    field = StrValueObjectField(Color, max_length=4)

    assert field.from_db_value("red", None, None) == Color("red")


def test_str_value_object_field_rejects_an_invalid_value_from_the_database() -> None:
    field = StrValueObjectField(Color, max_length=4)

    with pytest.raises(InvalidValueError) as excinfo:
        field.from_db_value("green", None, None)

    assert excinfo.value.code == "sample.invalid_color"


def test_str_value_object_field_parses_a_raw_string_for_the_admin() -> None:
    field = StrValueObjectField(Color, max_length=4)

    assert field.to_python("red") == Color("red")
    assert field.to_python(Color("blue")) == Color("blue")


def test_str_value_object_field_reports_an_invalid_value_as_a_validation_error() -> (
    None
):
    field = StrValueObjectField(Color, max_length=4)

    with pytest.raises(ValidationError) as excinfo:
        field.to_python("green")

    assert excinfo.value.code == "sample.invalid_color"


def test_str_value_object_field_survives_the_max_length_validator() -> None:
    field = StrValueObjectField(Color, max_length=4)

    assert field.clean(Color("blue"), None) == Color("blue")


def test_str_value_object_field_writes_the_plain_string() -> None:
    field = StrValueObjectField(Color, max_length=4)

    assert field.get_prep_value(Color("red")) == "red"
    assert field.get_prep_value("red") == "red"
    assert field.get_prep_value(None) is None


def test_str_value_object_field_deconstructs_to_a_migration_that_names_the_value_object() -> (
    None
):
    field = StrValueObjectField(Color, max_length=4)

    _name, path, args, kwargs = field.deconstruct()
    serialized, imports = MigrationWriter.serialize(field)

    assert path == "rastro.common.fields.StrValueObjectField"
    assert args == []
    assert kwargs == {"value_object": Color, "max_length": 4}
    assert "rastro.common.tests.sample.values.Color" in serialized
    assert "import rastro.common.tests.sample.values" in imports
