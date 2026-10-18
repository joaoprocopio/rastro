import importlib
import importlib.util
from collections import defaultdict
from collections.abc import Iterable
from enum import StrEnum
from types import ModuleType

from django.apps import apps

from rastro.common import errors as common_errors
from rastro.common.errors import ApplicationError
from rastro.common.middleware import STATUS_BY_CODE


def _error_modules() -> list[ModuleType]:
    modules = [common_errors]
    for config in apps.get_app_configs():
        module_name = f"{config.name}.errors"
        if config.name.startswith("rastro.") and importlib.util.find_spec(module_name):
            modules.append(importlib.import_module(module_name))
    return modules


def _error_classes(modules: Iterable[ModuleType]) -> list[type[ApplicationError]]:
    return [
        member
        for module in modules
        for member in vars(module).values()
        if isinstance(member, type)
        and issubclass(member, ApplicationError)
        and member is not ApplicationError
        and member.__module__ == module.__name__
    ]


def _owners_by_code(modules: Iterable[ModuleType]) -> dict[str, list[str]]:
    owners: dict[str, list[str]] = defaultdict(list)
    for module in modules:
        for name, member in vars(module).items():
            if not isinstance(member, type) or member.__module__ != module.__name__:
                continue
            if issubclass(member, ApplicationError) and member is not ApplicationError:
                owners[member.code].append(f"{module.__name__}.{name}")
            elif issubclass(member, StrEnum):
                for code in member:
                    owners[code.value].append(f"{module.__name__}.{name}.{code.name}")
    return owners


def _repeated_codes(modules: Iterable[ModuleType]) -> dict[str, list[str]]:
    return {
        code: owners
        for code, owners in _owners_by_code(modules).items()
        if len(owners) > 1
    }


def _module_with(name: str, **members: type) -> ModuleType:
    module = ModuleType(name)
    for member_name, member in members.items():
        member.__module__ = name
        setattr(module, member_name, member)
    return module


def test_no_error_code_repeats_across_apps() -> None:
    assert _repeated_codes(_error_modules()) == {}


def test_every_error_code_has_the_form_app_dot_name() -> None:
    codes = _owners_by_code(_error_modules())

    for code in codes:
        app, _, name = code.partition(".")
        assert app and name and name == name.lower(), code


def test_every_application_error_has_a_status() -> None:
    codes = {error.code for error in _error_classes(_error_modules())}

    assert codes <= STATUS_BY_CODE.keys()


def test_the_check_reports_a_code_that_two_apps_declare() -> None:
    class BookingTakenError(ApplicationError):
        code = "booking.taken"

    class SeatTakenError(ApplicationError):
        code = "booking.taken"

    modules = [
        _module_with("tests.booking.errors", BookingTakenError=BookingTakenError),
        _module_with("tests.seating.errors", SeatTakenError=SeatTakenError),
    ]

    assert _repeated_codes(modules) == {
        "booking.taken": [
            "tests.booking.errors.BookingTakenError",
            "tests.seating.errors.SeatTakenError",
        ]
    }
