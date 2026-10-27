import importlib
import pkgutil
from pathlib import Path

import rastro


def import_every_app_module(role: str) -> None:
    """Import `rastro.<app>.<role>` for each app that has it, as in `presentation.tasks`."""
    root = Path(rastro.__path__[0])
    path = Path(*role.split(".")).with_suffix(".py")
    for app in pkgutil.iter_modules(rastro.__path__):
        if (root / app.name / path).is_file():
            importlib.import_module(f"rastro.{app.name}.{role}")
