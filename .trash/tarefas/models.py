from django.db import models

from .infrastructure.models import TaskModel, SoftDeleteManager

__all__ = ["TaskModel", "SoftDeleteManager"]
