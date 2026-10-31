import importlib
import pkgutil
from pathlib import Path
from types import ModuleType

import rastro


def import_every_app_module(role: str) -> dict[str, ModuleType]:
    """Import `rastro.<app>.<role>` for each app that has it, keyed by the app label."""
    root = Path(rastro.__path__[0])
    path = Path(*role.split(".")).with_suffix(".py")
    return {
        app.name: importlib.import_module(f"rastro.{app.name}.{role}")
        for app in pkgutil.iter_modules(rastro.__path__)
        if (root / app.name / path).is_file()
    }
