from tests.architecture.rules import foreign_imports, module_source, values_modules


def test_every_values_module_imports_only_stdlib_pydantic_and_common_values() -> None:
    imports = [
        line
        for module in values_modules()
        for line in foreign_imports(source=module_source(module), name=module.__name__)
    ]

    assert imports == []


def test_the_check_reports_an_import_outside_the_standard_library() -> None:
    source = (
        "import re\n"
        "from typing import Annotated\n"
        "from pydantic import StringConstraints\n"
        "from rastro.common.values import ValueObject\n"
        "from django.db import models\n"
        "import pydantic_core\n"
        "from rastro.iam.models import Identity\n"
    )

    assert foreign_imports(source=source, name="tests.sample.values") == [
        "tests.sample.values:5: from django.db import models",
        "tests.sample.values:6: import pydantic_core",
        "tests.sample.values:7: from rastro.iam.models import Identity",
    ]
