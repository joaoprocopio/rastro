from enum import StrEnum

from django.db import models

from rastro.common.fields import StrEnumField
from rastro.common.models import BaseModel


class Status(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Post(BaseModel):
    status = StrEnumField(Status)


class Wall(BaseModel):
    coats = models.IntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(coats__gte=0), name="common_sample_wall_coats"
            ),
        ]
