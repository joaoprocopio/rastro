from typing import Protocol

from rastro.common.domain.aggregates import Aggregate
from tests.architecture.rules import (
    domain_classes,
    protocol_constructor_violations,
)


class Hasher(Protocol):
    def hash(self, *, password: str) -> str: ...


def test_no_domain_class_takes_a_protocol_in_its_constructor() -> None:
    assert protocol_constructor_violations(domain_classes()) == []


def test_the_check_finds_the_classes_of_every_domain_package() -> None:
    assert "rastro.common.tests.sample.domain.aggregates.Note" in [
        f"{cls.__module__}.{cls.__qualname__}" for cls in domain_classes()
    ]


def test_the_check_reports_a_constructor_that_takes_a_protocol() -> None:
    class Wall:
        def __init__(self, *, height: int, hasher: Hasher | None) -> None:
            self.hasher = hasher

    label = f"{__name__}.{Wall.__qualname__}"
    assert protocol_constructor_violations([Wall]) == [
        f"{label}: constructor takes the Protocol Hasher in 'hasher'"
    ]


def test_the_check_passes_an_aggregate_of_values_and_skips_a_protocol() -> None:
    class Brush(Aggregate):
        width: int

    assert protocol_constructor_violations([Brush, Hasher]) == []
