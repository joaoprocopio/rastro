import re
from typing import Optional

ALL_UPPER_SNAKE_CASE = re.compile(r"^[A-Z]+(_[A-Z]+)*$")


class BaseError(Exception):
    _registry: set[str] = set()

    code: str
    title: Optional[str]

    def __init__(self, title: Optional[str] = None) -> None:
        self.title = title

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

        if "code" not in cls.__dict__:  # type: ignore[misc]
            raise TypeError(f"{cls.__name__} must define 'code' attribute")

        code: str = cls.__dict__["code"]  # type: ignore[misc]

        if not ALL_UPPER_SNAKE_CASE.match(code):
            raise TypeError(f"Code must be UPPER_SNAKE_CASE: {code}")

        if code in cls._registry:
            raise ValueError(f"Duplicated error code: {code}")

        cls._registry.add(code)

    def _validate_code(self) -> None:
        if not ALL_UPPER_SNAKE_CASE.match(self.code):
            raise ValueError(f"Code must be UPPER_SNAKE_CASE, got: {self.code}")


print(BaseError._registry)


class InvalidIdError(BaseError):
    code = "INVALID_ABC"


print(BaseError._registry)


print(InvalidIdError())
