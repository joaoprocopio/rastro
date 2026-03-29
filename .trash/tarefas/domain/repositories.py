from datetime import datetime
from typing import Protocol

from .entities import Task
from .value_objects import TaskStatus


class TaskRepository(Protocol):
    def get_by_id(self, task_id: int, owner_id: int) -> Task | None: ...
    def list_by_owner(self, owner_id: int) -> list[Task]: ...
    def create(
        self,
        title: str,
        description: str | None,
        status: TaskStatus,
        owner_id: int,
    ) -> Task: ...
    def update(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        status: TaskStatus | None = None,
        owner_id: int | None = None,
    ) -> Task: ...
    def soft_delete(self, task_id: int, owner_id: int) -> bool: ...
