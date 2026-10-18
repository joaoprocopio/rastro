from tests.architecture.rules import pydantic_error_reads, rastro_sources

TRANSLATION_MODULES = ("rastro.common.problems", "rastro.common.fields")


def test_only_the_problems_and_fields_modules_read_pydantic_errors() -> None:
    reads = [
        read
        for name, source in rastro_sources()
        if name not in TRANSLATION_MODULES and "tests" not in name.split(".")
        for read in pydantic_error_reads(source=source, name=name)
    ]

    assert reads == []


def test_the_check_reports_each_way_to_reach_a_pydantic_error() -> None:
    source = (
        "import pydantic\n"
        "import pydantic_core\n"
        "from pydantic import BaseModel, ValidationError\n"
        "from pydantic_core import ErrorDetails\n"
        "from pydantic import StringConstraints\n"
        "pydantic.ValidationError\n"
        "pydantic.BaseModel\n"
    )

    assert pydantic_error_reads(source=source, name="rastro.sample.views") == [
        "rastro.sample.views:2: import pydantic_core",
        "rastro.sample.views:3: from pydantic import BaseModel, ValidationError",
        "rastro.sample.views:4: from pydantic_core import ErrorDetails",
        "rastro.sample.views:6: pydantic.ValidationError",
    ]
