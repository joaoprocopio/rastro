from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Optional


class BaseError(Exception, ABC):
    """Base class for every application error."""

    @property
    @abstractmethod
    def code(self) -> str: ...

    @property
    @abstractmethod
    def status(self) -> int: ...

    @property
    @abstractmethod
    def title(self) -> str: ...

    # per-occurrence, provided on instantiation
    detail: Optional[str] = None
    extensions: Optional[Mapping[str, object]] = None

    def __new__(cls, *args: object, **kwargs: object) -> "BaseError":
        if cls.__abstractmethods__:
            missing = ", ".join(sorted(cls.__abstractmethods__))
            raise TypeError(
                f"Can't instantiate abstract error {cls.__name__} missing: {missing}"
            )
        return super().__new__(cls)

    def __init__(
        self,
        detail: Optional[str] = None,
        *,
        extensions: Optional[Mapping[str, object]] = None,
    ) -> None:
        self.detail = detail
        self.extensions = extensions
        super().__init__(detail)
