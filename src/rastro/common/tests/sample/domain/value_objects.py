from typing import Annotated

from pydantic import StringConstraints

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
