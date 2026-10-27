from __future__ import annotations

from typing import ClassVar

from rastro.common.domain.schemas import Schema


def _name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


class BaseError(Exception):
    code: ClassVar[str]

    _class_by_code: ClassVar[dict[str, type[BaseError]]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "code" not in cls.__dict__:
            raise TypeError(f"{_name(cls)} declares no code.")
        if "status" in cls.__dict__:
            raise TypeError(
                f"{_name(cls)} declares a status, "
                "which belongs in an error-to-status table."
            )
        owner = BaseError._class_by_code.setdefault(cls.code, cls)
        if owner is not cls:
            raise TypeError(
                f"{_name(cls)} declares the code {cls.code!r}, "
                f"which {_name(owner)} already declares."
            )

    def __init__(self, extensions: Schema | None = None) -> None:
        super().__init__(self.code)
        self.extensions = extensions
