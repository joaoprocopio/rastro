from collections.abc import Callable
from types import ModuleType
from typing import Any


def module_with(name: str, *members: Callable[..., Any]) -> ModuleType:
    module = ModuleType(name)
    for member in members:
        member.__module__ = name
        setattr(module, member.__name__, member)
    return module
