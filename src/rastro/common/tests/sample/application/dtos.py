from rastro.common.application.dtos import DTO
from rastro.common.tests.sample.domain.value_objects import Color, Walls


class PaintApplyInput(DTO):
    color: Color
    coats: int
    walls: Walls | None = None
