from tests.architecture.rules import depends_uses, is_presentation, rastro_sources


def test_only_presentation_modules_use_depends() -> None:
    uses = [
        use
        for name, source in rastro_sources()
        if not is_presentation(name)
        for use in depends_uses(source=source, name=name)
    ]

    assert uses == []


def test_a_module_outside_a_presentation_package_is_not_presentation() -> None:
    assert [
        name
        for name in [
            "rastro.paint.presentation.dependencies",
            "rastro.paint.presentation.views",
            "rastro.paint.views",
            "rastro.paint.application.use_cases",
            "rastro.paint.domain.ports",
            "rastro.paint.infrastructure.adapters",
        ]
        if is_presentation(name)
    ] == [
        "rastro.paint.presentation.dependencies",
        "rastro.paint.presentation.views",
    ]


def test_the_check_reports_each_way_to_reach_depends() -> None:
    source = (
        "import fastapi\n"
        "import fastapi.params as params\n"
        "from fastapi import Depends, Request\n"
        "from fastapi.params import Depends as D\n"
        "from taskiq import TaskiqDepends\n"
        "fastapi.Depends\n"
        "params.Depends\n"
        "fastapi.Request\n"
        "TaskiqDepends()\n"
    )

    assert depends_uses(source=source, name="rastro.sample.services") == [
        "rastro.sample.services:3: from fastapi import Depends, Request",
        "rastro.sample.services:4: from fastapi.params import Depends as D",
        "rastro.sample.services:6: fastapi.Depends",
        "rastro.sample.services:7: params.Depends",
    ]
