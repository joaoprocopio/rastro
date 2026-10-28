from tests.architecture.rules import (
    depends_uses,
    depends_violations,
    is_presentation,
    rastro_sources,
)

DEPENDS_SOURCE = "from fastapi import Depends\n"


def test_only_presentation_modules_and_the_wiring_use_depends() -> None:
    assert depends_violations(rastro_sources()) == []


def test_the_wiring_exemption_covers_only_rastro_app() -> None:
    sources = [
        (name, DEPENDS_SOURCE)
        for name in [
            "rastro.app",
            "rastro.paint.presentation.views",
            "rastro.app.wiring",
            "rastro.apps",
            "rastro.paint.app",
            "rastro",
        ]
    ]

    assert depends_violations(sources) == [
        "rastro.app.wiring:1: from fastapi import Depends",
        "rastro.apps:1: from fastapi import Depends",
        "rastro.paint.app:1: from fastapi import Depends",
        "rastro:1: from fastapi import Depends",
    ]


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
