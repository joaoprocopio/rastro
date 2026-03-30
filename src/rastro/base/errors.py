import re
from collections.abc import Mapping

ALL_UPPER_SNAKE_CASE = re.compile(r"^[A-Z]+(_[A-Z]+)*$")


class BaseError(Exception):
    _registry: set[str] = set()

    __slots__ = ("title", "details")

    code: str
    title: str | None
    details: Mapping[str, object] | None

    def __init__(
        self,
        title: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        self.title = title
        self.details = details
        super().__init__(title)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

        if "code" not in cls.__dict__:  # type: ignore[misc]
            raise TypeError(f"{cls.__name__} must define 'code' attribute")

        code: str = cls.__dict__["code"]  # type: ignore[misc]

        if code in cls._registry:
            raise ValueError(f"Duplicate error code: {code}")

        if not ALL_UPPER_SNAKE_CASE.match(code):
            raise TypeError(f"Code must be UPPER_SNAKE_CASE: {code}")

        cls._registry.add(code)


class InvalidIdError(BaseError):
    code = "INVALID_ID"
