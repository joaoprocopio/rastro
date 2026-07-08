import re
from typing import Annotated

from pydantic import StringConstraints

from rastro_base.value_object import RootValueObject

# https://emailregex.com/
EMAIL_PATTERN = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


class Email(
    RootValueObject[
        Annotated[
            str,
            StringConstraints(to_lower=True, pattern=EMAIL_PATTERN),
        ]
    ]
):
    pass


class DisplayName(
    RootValueObject[
        Annotated[
            str,
            StringConstraints(max_length=320),
        ]
    ]
):
    pass


class RawPassword(
    RootValueObject[
        Annotated[
            str,
            StringConstraints(strip_whitespace=False, min_length=8),
        ]
    ]
):
    pass


class HashedPassword(RootValueObject[str]):
    pass
