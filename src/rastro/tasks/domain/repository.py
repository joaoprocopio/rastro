from abc import ABC, abstractmethod

from rastro.tasks.domain.entities import Task
from rastro.tasks.domain.value_objects import (
    TaskDescription,
    TaskDueDate,
    TaskPriority,
    TaskStatus,
    TaskTitle,
)
from rastro_base.entity import Id


class TaskRepository(ABC):
    @abstractmethod
    def create(
        self,
        title: TaskTitle,
        description: TaskDescription,
        status: TaskStatus,
        priority: TaskPriority,
        due_date: TaskDueDate,
        owner_id: Id,
        assignee_id: Id | None,
    ) -> Task: ...

    @abstractmethod
    def get_by_id(self, id: Id) -> Task | None: ...

    @abstractmethod
    def list_by_owner(self, owner_id: Id) -> list[Task]: ...

    @abstractmethod
    def list_by_assignee(self, assignee_id: Id) -> list[Task]: ...

    @abstractmethod
    def update(
        self,
        id: Id,
        title: TaskTitle | None = None,
        description: TaskDescription | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_date: TaskDueDate | None = None,
        assignee_id: Id | None = None,
    ) -> Task: ...

    @abstractmethod
    def delete(self, id: Id) -> None: ...
