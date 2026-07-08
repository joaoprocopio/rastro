from enum import StrEnum

from rastro_shared_kernel.utils import str_enum_to_choices


def test_str_enum_to_choices() -> None:
    class MockStatus(StrEnum):
        DRAFT = "draft"
        PUBLISHED = "published"

    choices = str_enum_to_choices(MockStatus)

    assert choices == [("draft", "DRAFT"), ("published", "PUBLISHED")]
