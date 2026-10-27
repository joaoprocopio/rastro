from pydantic import ConfigDict

from rastro.common.domain.schemas import Schema


class Aggregate(Schema):
    model_config = ConfigDict(frozen=False, validate_assignment=True)
