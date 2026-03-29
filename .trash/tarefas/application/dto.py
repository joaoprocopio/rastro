from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from rastro.tarefas.domain.value_objects import TaskStatus


class TaskOutput(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    owner_id: int
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


@dataclass(frozen=True)
class CreateTaskInput:
    title: str
    description: str | None
    owner_id: int


@dataclass(frozen=True)
class UpdateTaskInput:
    task_id: int
    owner_id: int
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None


@dataclass(frozen=True)
class GetTaskInput:
    task_id: int
    owner_id: int


@dataclass(frozen=True)
class DeleteTaskInput:
    task_id: int
    owner_id: int


@dataclass(frozen=True)
class ListTasksInput:
    owner_id: int
