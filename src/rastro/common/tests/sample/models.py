from enum import StrEnum

from rastro.common.fields import StrEnumField
from rastro.common.models import BaseModel


class Status(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Post(BaseModel):
    status = StrEnumField(Status)
