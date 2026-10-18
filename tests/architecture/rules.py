import ast
import importlib
import inspect
import pkgutil
import re
import sys
import typing
from enum import StrEnum
from pathlib import Path
from types import ModuleType, NoneType, UnionType
from typing import Any

from django.http import HttpRequest

import rastro

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")
RAW_TYPES = (str, dict)
FORBIDDEN_VALIDATION_METHODS = (
    "full_clean",
    "clean_fields",
    "validate_unique",
    "validate_constraints",
)
COMMON_VALUES = "rastro.common.values"


class Role(StrEnum):
    SERVICES = "services"
    SELECTORS = "selectors"


def logic_modules(role: Role) -> list[ModuleType]:
    modules: list[ModuleType] = []
    for app_dir in sorted(Path(rastro.__file__).parent.iterdir()):
        name = f"rastro.{app_dir.name}.{role}"
        if (app_dir / f"{role}.py").is_file():
            modules.append(importlib.import_module(name))
        elif (app_dir / role / "__init__.py").is_file():
            package = importlib.import_module(name)
            modules.append(package)
            for info in pkgutil.walk_packages(package.__path__, prefix=f"{name}."):
                modules.append(importlib.import_module(info.name))
    return modules


def values_modules() -> list[ModuleType]:
    return [
        importlib.import_module(f"rastro.{app_dir.name}.values")
        for app_dir in sorted(Path(rastro.__file__).parent.iterdir())
        if (app_dir / "values.py").is_file()
        and f"rastro.{app_dir.name}.values" != COMMON_VALUES
    ]


def rastro_sources() -> list[tuple[str, str]]:
    root = Path(rastro.__file__).parent
    return [
        (_module_name(path, root), path.read_text())
        for path in sorted(root.rglob("*.py"))
    ]


def module_source(module: ModuleType) -> str:
    assert module.__file__ is not None
    return Path(module.__file__).read_text()


def signature_violations(module: ModuleType, role: Role) -> list[str]:
    violations: list[str] = []
    for name, function in _public_functions(module):
        label = f"{module.__name__}.{name}"
        if NAME_PATTERN.match(name) is None:
            violations.append(f"{label}: name does not follow <entity>_<action>")
        signature = inspect.signature(function, eval_str=True)
        for parameter in signature.parameters.values():
            violations.extend(_argument_violations(label, parameter))
        violations.extend(_return_violations(label, role, signature.return_annotation))
    return violations


def django_conf_imports(*, source: str, name: str) -> list[str]:
    return [
        f"{name}:{node.lineno}: {ast.unparse(node)}"
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import | ast.ImportFrom) and _imports_django_conf(node)
    ]


def validation_violations(*, source: str, name: str) -> list[str]:
    violations: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in FORBIDDEN_VALIDATION_METHODS
        ):
            violations.append((node.lineno, f"calls {node.func.attr}()"))
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if (
                    isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
                    and item.name == "clean"
                ):
                    violations.append((item.lineno, f"{node.name} defines clean()"))
    return [f"{name}:{line}: {text}" for line, text in sorted(violations)]


def foreign_imports(*, source: str, name: str) -> list[str]:
    return [
        f"{name}:{node.lineno}: {ast.unparse(node)}"
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import | ast.ImportFrom)
        and not all(
            _is_allowed_in_values(imported) for imported in _imported_names(node)
        )
    ]


def _module_name(path: Path, root: Path) -> str:
    parts = path.relative_to(root.parent).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _imported_names(node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    return [node.module or ""] if node.level == 0 else [""]


def _is_allowed_in_values(imported: str) -> bool:
    return (
        imported == COMMON_VALUES
        or imported.partition(".")[0] in sys.stdlib_module_names
    )


def _public_functions(module: ModuleType) -> list[tuple[str, Any]]:
    return [
        (name, member)
        for name, member in vars(module).items()
        if inspect.isfunction(member)
        and not name.startswith("_")
        and member.__module__ == module.__name__
    ]


def _argument_violations(label: str, parameter: inspect.Parameter) -> list[str]:
    violations: list[str] = []
    prefix = f"{label}: argument '{parameter.name}'"
    if parameter.kind is not inspect.Parameter.KEYWORD_ONLY:
        violations.append(f"{prefix} is not keyword-only")
    annotation = parameter.annotation
    if annotation is inspect.Parameter.empty:
        violations.append(f"{prefix} has no type")
        return violations
    for raw_type in RAW_TYPES:
        if _mentions(annotation, raw_type):
            violations.append(f"{prefix} is a raw {raw_type.__name__}")
    if _mentions(annotation, HttpRequest) and parameter.name != "request":
        violations.append(
            f"{prefix} is an HttpRequest under a name other than 'request'"
        )
    if _is_dependency(annotation) and parameter.default is not inspect.Parameter.empty:
        violations.append(f"{label}: dependency '{parameter.name}' has a default")
    return violations


def _return_violations(label: str, role: Role, annotation: Any) -> list[str]:
    if annotation is inspect.Signature.empty:
        return [f"{label}: function has no return type"]
    if role is Role.SERVICES and annotation not in (None, NoneType):
        name = getattr(annotation, "__name__", repr(annotation))
        return [f"{label}: service returns {name} instead of None"]
    return []


def _members(annotation: Any) -> list[Any]:
    origin = typing.get_origin(annotation)
    if origin is UnionType or origin is typing.Union:
        return list(typing.get_args(annotation))
    return [origin or annotation]


def _mentions(annotation: Any, member: type) -> bool:
    return any(
        isinstance(candidate, type) and issubclass(candidate, member)
        for candidate in _members(annotation)
    )


def _is_dependency(annotation: Any) -> bool:
    return any(
        isinstance(candidate, type) and typing.is_protocol(candidate)
        for candidate in _members(annotation)
    )


def _imports_django_conf(node: ast.Import | ast.ImportFrom) -> bool:
    if isinstance(node, ast.Import):
        return any(_is_django_conf(alias.name) for alias in node.names)
    module = node.module or ""
    if module == "django":
        return any(alias.name == "conf" for alias in node.names)
    return _is_django_conf(module)


def _is_django_conf(module: str) -> bool:
    return module == "django.conf" or module.startswith("django.conf.")
