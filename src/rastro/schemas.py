from typing import Annotated

from pydantic import BeforeValidator

Csv = Annotated[
    list[str],
    BeforeValidator(
        lambda input: (
            [item.strip() for item in input.split(",")]
            if isinstance(input, str)
            else input
        )
    ),
]
