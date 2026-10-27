from rastro.common.domain.aggregates import Aggregate
from rastro.common.tests.sample.domain.value_objects import Color


class Note(Aggregate):
    id: int
    color: Color
