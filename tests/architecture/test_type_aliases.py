from tests.architecture.rules import rastro_sources, type_aliases


def test_every_data_type_is_a_class() -> None:
    aliases = [
        alias
        for name, source in rastro_sources()
        for alias in type_aliases(source=source, name=name)
    ]

    assert aliases == []


def test_the_check_reports_each_annotated_or_literal_alias() -> None:
    source = (
        "import typing\n"
        "from typing import Annotated, Literal, TypeAlias\n"
        "Width = Annotated[int, Field(ge=1)]\n"
        "Finish: TypeAlias = Literal['matte', 'gloss']\n"
        "type Coats = typing.Annotated[int, Field(le=3)]\n"
        "Brush = Annotated[Brush, Depends(brush)]\n"
        "Wall = fastapi_params.Depends\n"
        "WIDTHS = [Annotated[int, Field(ge=1)]]\n"
        "class Paint(RootValueObject[Annotated[str, Field(min_length=1)]]):\n"
        "    Shade = Literal['dark']\n"
    )

    assert type_aliases(source=source, name="rastro.paint.values") == [
        "rastro.paint.values:3: Width = Annotated[int, Field(ge=1)]",
        "rastro.paint.values:4: Finish: TypeAlias = Literal['matte', 'gloss']",
        "rastro.paint.values:5: type Coats = typing.Annotated[int, Field(le=3)]",
    ]
