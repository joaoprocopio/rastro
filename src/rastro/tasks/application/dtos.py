from dataclasses import dataclass
from datetime import datetime

from rastro_base.dto import DTO


@dataclass(frozen=True)
class CreateTaskInput(DTO):
    title: str
    description: str | None
    status: str
    priority: str
    due_date: datetime | None
    assignee_id: int | None


@dataclass(frozen=True)
class UpdateTaskInput(DTO):
    title: str | None
    description: str | None
    status: str | None
    priority: str | None
    due_date: datetime | None
    assignee_id: int | None


@dataclass(frozen=True)
class TaskOutput(DTO):
    id: int
    title: str
    description: str | None
    status: str
    priority: str
    due_date: datetime | None
    owner_id: int
    assignee_id: int | None
