from rastro.common.application.dtos import DTO
from rastro.common.tests.sample.domain.value_objects import Coats, Color


class PaintApplyInput(DTO):
    color: Color
    coats: Coats
