from pydantic import BaseModel, Field
from typing import Optional

from rastro.tarefas.domain.value_objects import TaskStatus


class CreateTaskForm(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class UpdateTaskForm(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
