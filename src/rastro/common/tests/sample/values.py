from typing import Annotated

from pydantic import StringConstraints

from rastro.common.values import ValueObject


class Color(
    ValueObject[
        Annotated[
            str, StringConstraints(min_length=3, max_length=6, pattern=r"^[a-z]+$")
        ]
    ]
):
    pass
