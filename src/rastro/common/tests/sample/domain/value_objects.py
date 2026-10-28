from typing import Annotated

from pydantic import Field, StringConstraints

from rastro.common.domain.value_objects import RootValueObject


class Color(
    RootValueObject[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True, min_length=3, max_length=6, pattern=r"^[a-z]+$"
            ),
        ]
    ]
):
    pass


# The problems module has no case for greater_than_equal, so a zero answers 500.
class Coats(RootValueObject[Annotated[int, Field(ge=1)]]):
    pass
