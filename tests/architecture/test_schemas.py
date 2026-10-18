import pydantic

from tests.architecture.helpers import module_with
from tests.architecture.rules import (
    app_modules,
    module_source,
    output_construction_violations,
    output_violations,
)


def test_every_output_schema_reads_its_model_from_attributes() -> None:
    violations = [
        violation
        for module in app_modules("schemas")
        for violation in output_violations(module)
    ]

    assert violations == []


def test_the_check_reports_an_output_schema_without_from_attributes() -> None:
    class WallPaintInput(pydantic.BaseModel):
        color: str

    class WallPaintOutput(pydantic.BaseModel):
        color: str

    class WallCountOutput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(from_attributes=True)

        count: int

    module = module_with(
        "rastro.sample.schemas", WallPaintInput, WallPaintOutput, WallCountOutput
    )

    assert output_violations(module) == [
        "rastro.sample.schemas.WallPaintOutput: Output schema does not set"
        " from_attributes",
    ]


def test_every_view_builds_its_output_from_the_model() -> None:
    violations = [
        violation
        for module in app_modules("views")
        for violation in output_construction_violations(
            source=module_source(module), name=module.__name__
        )
    ]

    assert violations == []


def test_the_check_reports_an_output_built_field_by_field() -> None:
    source = (
        "from rastro.sample import schemas\n"
        "from rastro.sample.schemas import WallPaintOutput\n"
        "WallPaintOutput.model_validate(wall)\n"
        "WallPaintOutput(color=wall.color)\n"
        "schemas.WallCountOutput(count=wall.count)\n"
    )

    assert output_construction_violations(
        source=source, name="rastro.sample.views"
    ) == [
        "rastro.sample.views:4: builds WallPaintOutput field by field",
        "rastro.sample.views:5: builds WallCountOutput field by field",
    ]
