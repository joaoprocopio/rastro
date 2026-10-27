from tests.architecture.rules import domain_modules, foreign_imports, module_source


def test_every_domain_module_imports_only_stdlib_pydantic_and_the_domain() -> None:
    imports = [
        line
        for module in domain_modules()
        for line in foreign_imports(source=module_source(module), name=module.__name__)
    ]

    assert imports == []


def test_the_check_finds_the_domain_of_every_app() -> None:
    names = [module.__name__ for module in domain_modules()]

    assert "rastro.common.domain.errors" in names
    assert "rastro.common.tests.sample.domain.aggregates" in names
    assert "rastro.auth.domain.value_objects" in names


def test_the_check_reports_an_import_outside_the_standard_library() -> None:
    source = (
        "import re\n"
        "from typing import Annotated\n"
        "from pydantic import StringConstraints\n"
        "from rastro.common.domain.value_objects import RootValueObject\n"
        "from sqlalchemy import String\n"
        "import pydantic_core\n"
        "from rastro.auth.infrastructure.models import UserRow\n"
        "from rastro.common.application.dtos import DTO\n"
    )

    assert foreign_imports(source=source, name="tests.sample.values") == [
        "tests.sample.values:5: from sqlalchemy import String",
        "tests.sample.values:6: import pydantic_core",
        "tests.sample.values:7: from rastro.auth.infrastructure.models import UserRow",
        "tests.sample.values:8: from rastro.common.application.dtos import DTO",
    ]
