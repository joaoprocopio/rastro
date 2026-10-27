from tests.architecture.rules import (
    is_use_case_module,
    rastro_sources,
    use_case_violations,
)


def test_every_use_case_is_async_with_required_keyword_only_dependencies() -> None:
    violations = [
        violation
        for name, source in rastro_sources()
        if is_use_case_module(name)
        for violation in use_case_violations(source=source, name=name)
    ]

    assert violations == []


def test_the_check_finds_the_use_case_modules_of_every_application_package() -> None:
    names = [name for name, _ in rastro_sources() if is_use_case_module(name)]

    assert "rastro.auth.application.use_cases" in names
    assert "rastro.common.tests.sample.application.use_cases" in names
    assert not is_use_case_module("rastro.paint.presentation.use_cases")


def test_the_check_reports_each_signature_that_breaks_the_rule() -> None:
    source = (
        "async def paint_apply(input, *, brush, wall): ...\n"
        "async def paint_mix(*, brush): ...\n"
        "def paint_dry(input, *, clock): ...\n"
        "async def paint_thin(input, brush): ...\n"
        "async def paint_strip(input, *, brush=None): ...\n"
        "async def paint_spray(input=None): ...\n"
        "async def paint_roll(*brushes): ...\n"
        "async def paint_wipe(input, **brushes): ...\n"
        "async def paint_sand(input, /): ...\n"
        "def _paint_helper(input, brush): ...\n"
    )

    assert use_case_violations(source=source, name="rastro.paint.use_cases") == [
        "rastro.paint.use_cases:3: paint_dry is not async",
        "rastro.paint.use_cases:4: paint_thin takes 'brush' by position",
        "rastro.paint.use_cases:5: paint_strip gives 'brush' a default",
        "rastro.paint.use_cases:6: paint_spray gives 'input' a default",
        "rastro.paint.use_cases:7: paint_roll takes '*brushes'",
        "rastro.paint.use_cases:8: paint_wipe takes '**brushes'",
    ]
