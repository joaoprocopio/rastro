import ast
import importlib
import inspect
import pkgutil
import sys
import typing
from collections.abc import Iterable, Mapping
from http import HTTPStatus
from pathlib import Path
from types import ModuleType, UnionType
from typing import Any

import pydantic

import rastro
from rastro.common.domain.errors import BaseError
from rastro.common.infrastructure.models import Row

PYDANTIC_ERROR = "ValidationError"
PYDANTIC_CORE = "pydantic_core"
FASTAPI = "fastapi"
DEPENDS = "Depends"
PRESENTATION = "presentation"
DOMAIN = "domain"
APPLICATION = "application"
USE_CASES = "use_cases"
ALIASED_FORMS = frozenset({"Annotated", "Literal"})
# create_app declares the CSRF check for every route.
WIRING = "rastro.app"


def domain_modules() -> list[ModuleType]:
    return rastro_modules(named=DOMAIN)


def rastro_modules(*, named: str) -> list[ModuleType]:
    """Import every module of rastro, tests included, whose dotted name has the part."""
    return [
        importlib.import_module(info.name)
        for info in pkgutil.walk_packages(rastro.__path__, prefix="rastro.")
        if named in info.name.split(".")
    ]


def error_classes() -> list[type[BaseError]]:
    return [
        member
        for module in rastro_modules(named="errors")
        for member in vars(module).values()
        if isinstance(member, type)
        and issubclass(member, BaseError)
        and member is not BaseError
        and member.__module__ == module.__name__
    ]


def status_violations(
    errors: Iterable[type[BaseError]], statuses: Mapping[type[BaseError], HTTPStatus]
) -> list[str]:
    return [
        f"{error.__module__}.{error.__qualname__}: no row in an error-to-status table"
        for error in errors
        if error not in statuses
    ]


def domain_classes() -> list[type]:
    return [
        member
        for module in rastro_modules(named=DOMAIN)
        for member in vars(module).values()
        if isinstance(member, type) and member.__module__ == module.__name__
    ]


def protocol_constructor_violations(classes: Iterable[type]) -> list[str]:
    return [
        f"{cls.__module__}.{cls.__qualname__}: constructor takes the Protocol "
        f"{candidate.__name__} in '{name}'"
        for cls in classes
        if not typing.is_protocol(cls)
        for name, annotation in _constructor_parameters(cls)
        for candidate in _members(annotation)
        if isinstance(candidate, type) and typing.is_protocol(candidate)
    ]


def _constructor_parameters(cls: type) -> list[tuple[str, Any]]:
    if issubclass(cls, pydantic.BaseModel):
        return [(name, field.annotation) for name, field in cls.model_fields.items()]
    signature = inspect.signature(cls.__init__, eval_str=True)
    return [
        (parameter.name, parameter.annotation)
        for parameter in list(signature.parameters.values())[1:]
    ]


def mapped_tables() -> list[type]:
    rastro_modules(named="models")
    return sorted(
        (mapper.class_ for mapper in Row.registry.mappers), key=_qualified_name
    )


def table_violations(tables: list[type]) -> list[str]:
    violations: list[str] = []
    for table in tables:
        label = _qualified_name(table)
        if not issubclass(table, Row):
            violations.append(f"{label}: does not subclass {_qualified_name(Row)}")
        prefix = f"{table.__module__.split('.')[1]}_"
        name = str(vars(table)["__tablename__"])
        if not name.startswith(prefix):
            violations.append(
                f"{label}: table name {name!r} does not start with {prefix!r}"
            )
    return violations


def _qualified_name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__name__}"


def rastro_sources() -> list[tuple[str, str]]:
    root = Path(rastro.__file__).parent
    return [
        (_module_name(path, root), path.read_text())
        for path in sorted(root.rglob("*.py"))
    ]


def module_source(module: ModuleType) -> str:
    assert module.__file__ is not None
    return Path(module.__file__).read_text()


def foreign_imports(*, source: str, name: str) -> list[str]:
    return [
        f"{name}:{node.lineno}: {ast.unparse(node)}"
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import | ast.ImportFrom)
        and not all(
            _is_allowed_in_the_domain(imported) for imported in _imported_names(node)
        )
    ]


def pydantic_error_reads(*, source: str, name: str) -> list[str]:
    tree = ast.parse(source)
    pydantic_names = _pydantic_module_names(tree)
    return [
        f"{name}:{node.lineno}: {ast.unparse(node)}"
        for node in ast.walk(tree)
        if isinstance(node, ast.stmt | ast.expr)
        and _reads_pydantic_error(node, pydantic_names)
    ]


def is_presentation(name: str) -> bool:
    return PRESENTATION in name.split(".")


def depends_violations(sources: Iterable[tuple[str, str]]) -> list[str]:
    return [
        use
        for name, source in sources
        if not is_presentation(name) and name != WIRING
        for use in depends_uses(source=source, name=name)
    ]


def depends_uses(*, source: str, name: str) -> list[str]:
    tree = ast.parse(source)
    fastapi_names = _fastapi_module_names(tree)
    return [
        f"{name}:{node.lineno}: {ast.unparse(node)}"
        for node in ast.walk(tree)
        if isinstance(node, ast.stmt | ast.expr) and _uses_depends(node, fastapi_names)
    ]


def type_aliases(*, source: str, name: str) -> list[str]:
    return [
        f"{name}:{node.lineno}: {ast.unparse(node)}"
        for node in ast.parse(source).body
        if (value := _alias_value(node)) is not None
        and _subscripted_form(value) in ALIASED_FORMS
        and not _mentions_depends(value)
    ]


def _alias_value(node: ast.stmt) -> ast.expr | None:
    match node:
        case ast.Assign(targets=[ast.Name()], value=value):
            return value
        case ast.AnnAssign(target=ast.Name(), value=value) | ast.TypeAlias(value=value):
            return value
    return None


def _subscripted_form(node: ast.expr) -> str | None:
    match node:
        case ast.Subscript(value=ast.Name(id=form) | ast.Attribute(attr=form)):
            return form
    return None


def _mentions_depends(node: ast.expr) -> bool:
    return any(
        isinstance(child, ast.Name)
        and child.id == DEPENDS
        or isinstance(child, ast.Attribute)
        and child.attr == DEPENDS
        for child in ast.walk(node)
    )


def is_use_case_module(name: str) -> bool:
    parts = name.split(".")
    return len(parts) >= 2 and parts[-2:] == [APPLICATION, USE_CASES]


def use_case_violations(*, source: str, name: str) -> list[str]:
    """Report each public function that is not async or takes a dependency loosely."""
    return [
        f"{name}:{node.lineno}: {node.name} {problem}"
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
        for problem in _use_case_problems(node)
    ]


def _use_case_problems(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    arguments = node.args
    positional = [*arguments.posonlyargs, *arguments.args]
    keyword_defaults = zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True)
    return [
        *(["is not async"] if isinstance(node, ast.FunctionDef) else []),
        *(f"takes {argument.arg!r} by position" for argument in positional[1:]),
        *(
            f"gives {argument.arg!r} a default"
            for argument in positional[len(positional) - len(arguments.defaults) :]
        ),
        *(
            f"gives {argument.arg!r} a default"
            for argument, default in keyword_defaults
            if default is not None
        ),
        *([f"takes '*{arguments.vararg.arg}'"] if arguments.vararg else []),
        *([f"takes '**{arguments.kwarg.arg}'"] if arguments.kwarg else []),
    ]


def _fastapi_module_names(tree: ast.Module) -> set[str]:
    return {
        alias.asname or alias.name.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if _is_fastapi(alias.name)
    }


def _uses_depends(node: ast.stmt | ast.expr, fastapi_names: set[str]) -> bool:
    match node:
        case ast.ImportFrom(module=str(module), names=names) if _is_fastapi(module):
            return any(alias.name == DEPENDS for alias in names)
        case ast.Attribute(attr=attr, value=value) if attr == DEPENDS:
            return _root_name(value) in fastapi_names
        case _:
            return False


def _root_name(node: ast.expr) -> str | None:
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _is_fastapi(module: str) -> bool:
    return module == FASTAPI or module.startswith(f"{FASTAPI}.")


def _module_name(path: Path, root: Path) -> str:
    parts = path.relative_to(root.parent).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _imported_names(node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    return [node.module or ""] if node.level == 0 else [""]


def _is_allowed_in_the_domain(imported: str) -> bool:
    parts = imported.split(".")
    return (
        imported == "pydantic"
        or parts[0] in sys.stdlib_module_names
        or (parts[0] == "rastro" and DOMAIN in parts)
    )


def _pydantic_module_names(tree: ast.Module) -> set[str]:
    return {
        alias.asname or "pydantic"
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "pydantic" or alias.name.startswith("pydantic.")
    }


def _reads_pydantic_error(node: ast.stmt | ast.expr, pydantic_names: set[str]) -> bool:
    match node:
        case ast.Import(names=names):
            return any(_is_pydantic_core(alias.name) for alias in names)
        case ast.ImportFrom(module="pydantic", names=names):
            return any(alias.name == PYDANTIC_ERROR for alias in names)
        case ast.ImportFrom(module=str(module)):
            return _is_pydantic_core(module)
        case ast.Attribute(value=ast.Name(id=module_name), attr=attr):
            return module_name in pydantic_names and attr == PYDANTIC_ERROR
        case _:
            return False


def _is_pydantic_core(module: str) -> bool:
    return module == PYDANTIC_CORE or module.startswith(f"{PYDANTIC_CORE}.")


def _members(annotation: Any) -> list[Any]:
    origin = typing.get_origin(annotation)
    if origin is UnionType or origin is typing.Union:
        return list(typing.get_args(annotation))
    return [origin or annotation]
